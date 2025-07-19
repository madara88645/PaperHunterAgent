import PyPDF2
import pdfplumber
import requests
import re
import logging
from typing import Dict, List, Optional, Any
from io import BytesIO


class SummarizerAgent:
    """
    SummarizerAgent in the QuantumResearchChain.
    Mission: Create a concise but information-dense summary of a single quantum-science paper.
    """
    
    def __init__(self):
        """Initialize the SummarizerAgent."""
        self.logger = logging.getLogger(__name__)
        
    def extract_pdf_text(self, pdf_url: str) -> Optional[str]:
        """
        Extract text from PDF URL.
        
        Args:
            pdf_url: URL to the PDF file
            
        Returns:
            Extracted text or None if failed
        """
        try:
            # Download PDF
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()
            
            # Try with pdfplumber first (better for layout)
            try:
                with pdfplumber.open(BytesIO(response.content)) as pdf:
                    text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    return text if text.strip() else None
            except Exception:
                # Fallback to PyPDF2
                try:
                    pdf_reader = PyPDF2.PdfReader(BytesIO(response.content))
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text if text.strip() else None
                except Exception as e:
                    self.logger.error(f"Failed to extract PDF text: {e}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Failed to download or process PDF from {pdf_url}: {e}")
            return None
    
    def extract_equations(self, text: str) -> List[str]:
        """
        Extract LaTeX equations from text.
        
        Args:
            text: PDF text content
            
        Returns:
            List of equation strings with labels
        """
        equations = []
        
        # Look for common LaTeX equation patterns
        patterns = [
            r'\$\$([^$]+)\$\$',  # Display math
            r'\\\[([^\]]+)\\\]',  # LaTeX display
            r'\\begin\{equation\}(.*?)\\end\{equation\}',  # Equation environment
            r'\\begin\{align\}(.*?)\\end\{align\}',  # Align environment
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for i, match in enumerate(matches[:3]):  # Limit to 3 equations
                cleaned = match.strip()
                if cleaned and len(cleaned) > 10:  # Skip trivial equations
                    equations.append(f"Eq. {len(equations) + 1}: {cleaned}")
                    
        return equations[:3]  # Max 3 equations
    
    def identify_primary_topic(self, title: str, abstract: str) -> str:
        """
        Identify the primary topic of the paper.
        
        Args:
            title: Paper title
            abstract: Paper abstract
            
        Returns:
            Primary topic string
        """
        text = f"{title} {abstract}".lower()
        
        # Topic mapping based on keywords
        topics = {
            "Quantum Error Correction": ["error correction", "quantum error", "surface code", "stabilizer"],
            "Quantum Computing": ["quantum computer", "quantum algorithm", "qubit", "quantum gate"],
            "Quantum Cryptography": ["quantum cryptography", "quantum key distribution", "qkd"],
            "Quantum Communication": ["quantum communication", "quantum network", "quantum internet"],
            "Quantum Sensing": ["quantum sensing", "quantum metrology", "magnetometry"],
            "Quantum Field Theory": ["quantum field theory", "qft", "field theory"],
            "Condensed Matter": ["condensed matter", "solid state", "many-body"],
            "Quantum Machine Learning": ["quantum machine learning", "qml", "quantum neural"],
            "Quantum Optics": ["quantum optics", "photonic", "optical quantum"],
            "Quantum Information": ["quantum information", "entanglement", "quantum state"]
        }
        
        for topic, keywords in topics.items():
            if any(keyword in text for keyword in keywords):
                return topic
                
        return "Quantum Physics"  # Default
    
    def generate_tldr(self, abstract: str, full_text: str) -> str:
        """
        Generate a TL;DR summary (≤120 words).
        
        Args:
            abstract: Paper abstract
            full_text: Full paper text
            
        Returns:
            TL;DR summary
        """
        # Use abstract as base, but enhance with key findings from text
        words = abstract.split()
        
        # Extract key phrases from conclusions/results sections
        conclusion_patterns = [
            r'conclusion[s]?[:\.]?\s*([^.]*\.)',
            r'result[s]?[:\.]?\s*([^.]*\.)',
            r'we show[ed]?\s*([^.]*\.)',
            r'we demonstrate[d]?\s*([^.]*\.)',
            r'our findings\s*([^.]*\.)'
        ]
        
        key_findings = []
        for pattern in conclusion_patterns:
            matches = re.findall(pattern, full_text.lower(), re.IGNORECASE)
            key_findings.extend(matches[:2])  # Limit findings
            
        # Combine abstract with key findings
        tldr_text = abstract
        if key_findings:
            tldr_text += " " + " ".join(key_findings[:2])
            
        # Truncate to 120 words
        words = tldr_text.split()[:120]
        return " ".join(words)
    
    def extract_contributions(self, full_text: str) -> List[str]:
        """
        Extract main contributions from the paper.
        
        Args:
            full_text: Full paper text
            
        Returns:
            List of contribution bullet points
        """
        contributions = []
        
        # Look for contribution sections or patterns
        patterns = [
            r'contribution[s]?[:\.]?\s*([^.]*\.)',
            r'we propose\s*([^.]*\.)',
            r'novel[ty]?\s*([^.]*\.)',
            r'key insight[s]?\s*([^.]*\.)',
            r'main result[s]?\s*([^.]*\.)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, full_text.lower(), re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 20:  # Skip trivial matches
                    contributions.append(f"• {match.strip().capitalize()}")
                    
        return contributions[:5]  # Limit to 5 contributions
    
    def extract_glossary_terms(self, full_text: str) -> Dict[str, str]:
        """
        Extract technical terms and their definitions.
        
        Args:
            full_text: Full paper text
            
        Returns:
            Dictionary of terms and their definitions
        """
        glossary = {}
        
        # Common quantum physics terms
        quantum_terms = [
            "qubit", "superposition", "entanglement", "decoherence", "fidelity",
            "hamiltonian", "pauli", "bloch sphere", "quantum gate", "circuit depth",
            "ancilla", "syndrome", "stabilizer", "logical qubit", "error rate"
        ]
        
        for term in quantum_terms:
            # Look for definitions (term followed by explanation)
            pattern = f"{term}[s]?\\s*(?:is|are|refers to|denotes)\\s*([^.]*\\.)"
            matches = re.findall(pattern, full_text.lower(), re.IGNORECASE)
            
            if matches and len(matches[0].split()) <= 12:  # Max 12 words
                glossary[term.title()] = matches[0].strip()
                
            if len(glossary) >= 6:  # Limit to 6 terms
                break
                
        return glossary
    
    def create_summary(self, paper_data: Dict[str, Any]) -> str:
        """
        Create a complete summary for a paper.
        
        Args:
            paper_data: Paper metadata and content
            
        Returns:
            Markdown formatted summary
        """
        try:
            # Extract PDF text
            pdf_text = self.extract_pdf_text(paper_data["url_pdf"])
            
            if not pdf_text:
                return "⚠️ Unable to parse PDF"
                
            # Extract components
            equations = self.extract_equations(pdf_text)
            primary_topic = self.identify_primary_topic(paper_data["title"], paper_data["abstract"])
            tldr = self.generate_tldr(paper_data["abstract"], pdf_text)
            contributions = self.extract_contributions(pdf_text)
            glossary = self.extract_glossary_terms(pdf_text)
            
            # Format authors
            authors_str = ", ".join(paper_data["authors"])
            
            # Build markdown summary
            summary = f"""# {paper_data["title"]}

| Field | Value |
|-------|-------|
| Authors | {authors_str} |
| Published | {paper_data["published"]} |
| Primary Topic | {primary_topic} |
| Key Equations | {", ".join(equations[:3]) if equations else "None found"} |

## TL;DR (≤ 120 words)
{tldr}

## Main Contributions
{chr(10).join(contributions) if contributions else "• Contributions not clearly identified"}

## Critical Assessment
**Why it matters:** This work advances our understanding of {primary_topic.lower()} by providing new insights into quantum systems. The research contributes to the growing body of knowledge in quantum science with practical implications.

**Potential weaknesses:** The methodology may have limitations that require further validation in different experimental conditions.

## Glossary
| Term | Definition (≤ 12 words) |
|------|-------------------------|"""
            
            for term, definition in glossary.items():
                summary += f"\n| {term} | {definition} |"
                
            if not glossary:
                summary += "\n| No terms | Glossary terms not identified |"
                
            return summary
            
        except Exception as e:
            self.logger.error(f"Error creating summary: {e}")
            return "⚠️ Unable to parse PDF"
