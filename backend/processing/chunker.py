import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List

from langchain.text_splitter import RecursiveCharacterTextSplitter

from backend.config.pipeline_config import ChunkConfig, ChunkingProfile
from backend.utils.token_estimator import estimate_tokens


class Chunker:
    """
    A chunker for splitting extracted document content into smaller pieces.

    This class is optimized for creating chunks of a target token size, which is
    ideal for downstream tasks like Retrieval-Augmented Generation (RAG). It
    includes logic for automatically selecting chunking profiles based on
    content complexity.
    """

    def __init__(self, key_lang: str = "en"):
        """
        Initializes the Chunker.

        Args:
            key_lang: The primary language of the content being chunked.
        """
        self.key_lang = key_lang
        self.chunk_stats = {
            "total_pages": 0,
            "total_chunks": 0,
            "chunks_per_page": [],
            "token_distribution": [],
            "empty_pages": 0,
            "processing_errors": [],
        }

    def chunk_extraction_result(
        self, extraction_results: List[Dict], auto_profile: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Chunks the results of an extraction process.

        This method iterates through the extraction results for each page,
        formats the content, and splits it into chunks based on the selected
        chunking profile.

        Args:
            extraction_results: A list of dictionaries, where each dictionary
                                represents the extracted content of a page.
            auto_profile: If True, automatically selects a chunking profile
                          based on the content of each page.

        Returns:
            A list of dictionaries, where each dictionary represents a chunk.
        """
        all_chunks = []
        for i, result in enumerate(extraction_results):
            try:
                if not self._validate_page_result(result):
                    self.chunk_stats["empty_pages"] += 1
                    continue

                profile = (
                    self._auto_select_profile(result)
                    if auto_profile
                    else ChunkingProfile.STANDARD
                )
                config = self._get_chunking_config(profile)

                page_chunks = self._process_page(result, config, i)
                valid_chunks = [
                    chunk for chunk in page_chunks if self._validate_chunk(chunk)
                ]
                all_chunks.extend(valid_chunks)

                self.chunk_stats["total_pages"] += 1
                self.chunk_stats["chunks_per_page"].append(len(valid_chunks))
            except Exception as e:
                self.chunk_stats["processing_errors"].append(
                    {"page_idx": i, "error": str(e)}
                )
                continue

        self.chunk_stats["total_chunks"] = len(all_chunks)
        return all_chunks

    def _validate_page_result(self, result: Dict) -> bool:
        """
        Validates that a page result has extractable content.
        """
        if not result:
            return False
        return any(
            result.get(key)
            for key in ["main_title", "page_summary", "key_sections", "tables", "visual_elements"]
        )

    def _validate_chunk(self, chunk: Dict) -> bool:
        """
        Validates that a chunk has meaningful content.
        """
        if not chunk:
            return False
        page_content = chunk.get("page_content", "")
        return page_content and len(page_content.strip()) >= 10

    def _auto_select_profile(self, result: Dict) -> ChunkingProfile:
        """
        Automatically selects the best chunking profile based on content complexity.
        """
        complexity = result.get("page_complexity", "moderate")
        tables = result.get("tables", [])
        if complexity == "extreme" or len(tables) > 3:
            return ChunkingProfile.COMPLEX_TABLES
        if complexity == "simple" and not tables:
            return ChunkingProfile.SIMPLE
        return ChunkingProfile.STANDARD

    def _get_chunking_config(self, profile: ChunkingProfile) -> ChunkConfig:
        """
        Returns the chunking configuration for a given profile.
        """
        # In a real scenario, these profiles would be loaded from a config file.
        profiles = {
            ChunkingProfile.STANDARD: {
                "chunk_size": 3000,
                "chunk_overlap": 200,
                "separators": ["\n\n\n", "\n\n", "\n", ". "],
            },
            ChunkingProfile.COMPLEX_TABLES: {
                "chunk_size": 4000,
                "chunk_overlap": 300,
                "separators": ["\n\n\n", "\n\n"],
            },
            ChunkingProfile.SIMPLE: {
                "chunk_size": 2000,
                "chunk_overlap": 100,
                "separators": ["\n\n", "\n", ". ", " "],
            },
        }
        config_data = profiles[profile]
        return ChunkConfig(profile=profile.value, **config_data)

    def _process_page(
        self, result: Dict, config: ChunkConfig, page_idx: int
    ) -> List[Dict]:
        """
        Processes a single page, splitting it into chunks if necessary.
        """
        page_content = self._create_page_content(result)
        if not page_content.strip():
            return []

        token_count = estimate_tokens(page_content)
        self.chunk_stats["token_distribution"].append(token_count)

        base_metadata = self._create_base_metadata(result, page_idx, config.profile)

        if token_count <= config.chunk_size:
            return [
                {
                    "page_content": page_content,
                    "metadata": {
                        **base_metadata,
                        "is_full_page": True,
                        "chunk_index": 0,
                        "total_chunks": 1,
                        "estimated_tokens": token_count,
                    },
                    "embedding_id": self._generate_chunk_id(page_content, base_metadata),
                }
            ]
        else:
            return self._split_large_page(page_content, base_metadata, config)

    def _create_page_content(self, result: Dict) -> str:
        """
        Creates a comprehensive page content string optimized for RAG.
        """
        sections = []
        if result.get("main_title"):
            sections.append(f"# {result['main_title']}")
        if result.get("page_summary"):
            sections.append(f"## Summary\n{result['page_summary']}")
        
        # Simplified content formatting for brevity
        if result.get("key_sections"):
            for section in result["key_sections"]:
                title = section.get("section_title", "Content")
                content = section.get("content", "")
                if isinstance(content, list):
                    content = "\n".join(f"- {item}" for item in content)
                sections.append(f"### {title}\n{content}")

        return "\n\n---\n\n".join(sections)

    def _create_base_metadata(
        self, result: Dict, page_idx: int, profile: str
    ) -> Dict:
        """
        Creates a base metadata dictionary for a chunk.
        """
        page_number = result.get("metadata", {}).get("page_number", page_idx)
        return {
            "page_number": page_number,
            "page_title": result.get("main_title", ""),
            "page_summary": result.get("page_summary", ""),
            "page_complexity": result.get("page_complexity", "moderate"),
            "language": self.key_lang,
            "chunking_profile": profile,
            "chunked_at": datetime.now().isoformat(),
        }

    def _split_large_page(
        self, content: str, metadata: Dict, config: ChunkConfig
    ) -> List[Dict]:
        """
        Splits a large page into multiple chunks using a text splitter.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=config.separators,
            length_function=estimate_tokens,
        )
        texts = splitter.split_text(content)
        chunks = []
        for i, text in enumerate(texts):
            chunk_metadata = {
                **metadata,
                "is_full_page": False,
                "chunk_index": i,
                "total_chunks": len(texts),
                "estimated_tokens": estimate_tokens(text),
            }
            chunks.append(
                {
                    "page_content": text,
                    "metadata": chunk_metadata,
                    "embedding_id": self._generate_chunk_id(text, chunk_metadata),
                }
            )
        return chunks

    def _generate_chunk_id(self, content: str, metadata: Dict) -> str:
        """
        Generates a unique, deterministic ID for a chunk.
        """
        id_content = f"{metadata['page_number']}_{metadata.get('chunk_index', 0)}_{content[:100]}"
        return hashlib.md5(id_content.encode()).hexdigest()

    def get_chunking_stats(self) -> Dict:
        """
        Returns statistics about the chunking process.
        """
        stats = self.chunk_stats.copy()
        if stats["chunks_per_page"]:
            stats["avg_chunks_per_page"] = sum(stats["chunks_per_page"]) / len(
                stats["chunks_per_page"]
            )
        if stats["token_distribution"]:
            stats["avg_tokens_per_page"] = sum(stats["token_distribution"]) / len(
                stats["token_distribution"]
            )
        return stats
