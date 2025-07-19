import re
import logging
from typing import List, Dict, Set, Tuple


class ConceptMapAgent:
    """
    ConceptMapAgent in the QuantumResearchChain.
    Objective: Transform a SummarizerAgent report into a machine-readable concept graph.
    """
    
    def __init__(self):
        """Initialize the ConceptMapAgent."""
        self.logger = logging.getLogger(__name__)
        self.max_nodes = 20
        self.max_edges = 30
        
    def extract_entities(self, summary_text: str) -> Set[str]:
        """
        Extract entities from the summary text.
        
        Args:
            summary_text: Markdown summary from SummarizerAgent
            
        Returns:
            Set of entity strings
        """
        entities = set()
        
        # Extract from title
        title_match = re.search(r'^# (.+)$', summary_text, re.MULTILINE)
        if title_match:
            title_words = self._extract_key_phrases(title_match.group(1))
            entities.update(title_words)
            
        # Extract from primary topic
        topic_match = re.search(r'\| Primary Topic \| (.+) \|', summary_text)
        if topic_match:
            entities.add(self._normalize_entity(topic_match.group(1)))
            
        # Extract from TL;DR
        tldr_match = re.search(r'## TL;DR.*?\n(.+?)(?=\n##|\n\||\Z)', summary_text, re.DOTALL)
        if tldr_match:
            tldr_entities = self._extract_key_phrases(tldr_match.group(1))
            entities.update(tldr_entities)
            
        # Extract from contributions
        contrib_match = re.search(r'## Main Contributions\n(.+?)(?=\n##|\Z)', summary_text, re.DOTALL)
        if contrib_match:
            contrib_entities = self._extract_key_phrases(contrib_match.group(1))
            entities.update(contrib_entities)
            
        # Extract from glossary terms
        glossary_matches = re.findall(r'\| ([^|]+) \| [^|]+ \|', summary_text)
        for term in glossary_matches:
            if term.strip() != "Term" and term.strip() != "No terms":
                entities.add(self._normalize_entity(term.strip()))
                
        return entities
    
    def extract_relationships(self, summary_text: str, entities: Set[str]) -> List[Tuple[str, str, str]]:
        """
        Extract relationships between entities.
        
        Args:
            summary_text: Markdown summary text
            entities: Set of extracted entities
            
        Returns:
            List of (source, relation, target) tuples
        """
        relationships = []
        
        # Define relationship patterns
        relation_patterns = {
            "extends": [r"extend[s]?", r"build[s]? upon", r"generalize[s]?"],
            "depends_on": [r"depend[s]? on", r"require[s]?", r"need[s]?", r"use[s]?"],
            "measures": [r"measure[s]?", r"quantif[y|ies]", r"detect[s]?"],
            "implements": [r"implement[s]?", r"realize[s]?", r"demonstrate[s]?"],
            "improves": [r"improve[s]?", r"enhance[s]?", r"optimize[s]?"],
            "enables": [r"enable[s]?", r"allow[s]?", r"facilitate[s]?"],
            "corrects": [r"correct[s]?", r"fix[es]?", r"mitigate[s]?"],
            "applies": [r"appl[y|ies]", r"utilize[s]?", r"employ[s]?"]
        }
        
        # Extract relationships from text
        text_lower = summary_text.lower()
        entity_list = list(entities)
        
        for i, entity1 in enumerate(entity_list):
            for j, entity2 in enumerate(entity_list):
                if i != j:
                    for relation, patterns in relation_patterns.items():
                        for pattern in patterns:
                            # Check if entities appear with relationship pattern
                            regex_pattern = f"{re.escape(entity1.lower())}.*?{pattern}.*?{re.escape(entity2.lower())}"
                            if re.search(regex_pattern, text_lower):
                                relationships.append((
                                    self._to_snake_case(entity1),
                                    relation,
                                    self._to_snake_case(entity2)
                                ))
                                break
                                
        # Add some domain-specific relationships
        domain_relationships = self._add_domain_relationships(entities)
        relationships.extend(domain_relationships)
        
        return relationships[:self.max_edges]
    
    def generate_mermaid_diagram(self, entities: Set[str], relationships: List[Tuple[str, str, str]]) -> str:
        """
        Generate Mermaid diagram code.
        
        Args:
            entities: Set of entity strings
            relationships: List of relationship tuples
            
        Returns:
            Mermaid diagram code
        """
        # Limit entities
        limited_entities = list(entities)[:self.max_nodes]
        
        # Build node definitions
        nodes = {}
        for entity in limited_entities:
            node_id = self._to_snake_case(entity)
            node_label = self._truncate_label(entity)
            nodes[node_id] = node_label
            
        # Build diagram
        diagram_lines = ["graph TD"]
        
        # Add relationships
        used_nodes = set()
        for source, relation, target in relationships:
            if source in nodes and target in nodes:
                source_label = nodes[source]
                target_label = nodes[target]
                diagram_lines.append(f"    {source}[{source_label}] -->|{relation}| {target}[{target_label}]")
                used_nodes.add(source)
                used_nodes.add(target)
                
        # Add standalone nodes if they don't appear in relationships
        for node_id, label in nodes.items():
            if node_id not in used_nodes:
                diagram_lines.append(f"    {node_id}[{label}]")
                
        return "\n".join(diagram_lines)
    
    def create_concept_map(self, summary_text: str) -> str:
        """
        Main method to create concept map from summary.
        
        Args:
            summary_text: Markdown summary from SummarizerAgent
            
        Returns:
            Mermaid diagram code
        """
        try:
            # Extract entities and relationships
            entities = self.extract_entities(summary_text)
            relationships = self.extract_relationships(summary_text, entities)
            
            # Generate Mermaid diagram
            diagram = self.generate_mermaid_diagram(entities, relationships)
            
            return diagram
            
        except Exception as e:
            self.logger.error(f"Error creating concept map: {e}")
            return "graph TD\n    error[Error creating concept map]"
    
    def _extract_key_phrases(self, text: str) -> Set[str]:
        """Extract key phrases from text."""
        # Remove markdown and clean text
        clean_text = re.sub(r'[#*_`]', '', text)
        clean_text = re.sub(r'\|[^|]*\|', '', clean_text)  # Remove table cells
        
        # Extract noun phrases and technical terms
        phrases = set()
        
        # Quantum physics terms
        quantum_terms = [
            "quantum computer", "quantum algorithm", "quantum gate", "quantum circuit",
            "quantum error correction", "error correction", "surface code", "logical qubit",
            "physical qubit", "quantum state", "superposition", "entanglement",
            "decoherence", "quantum noise", "fidelity", "syndrome measurement",
            "stabilizer code", "pauli operator", "hamiltonian", "quantum channel"
        ]
        
        text_lower = clean_text.lower()
        for term in quantum_terms:
            if term in text_lower:
                phrases.add(self._normalize_entity(term))
                
        # Extract capitalized phrases (likely important concepts)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', clean_text)
        for phrase in capitalized:
            if len(phrase.split()) <= 4:  # Max 4 words
                phrases.add(self._normalize_entity(phrase))
                
        return phrases
    
    def _normalize_entity(self, entity: str) -> str:
        """Normalize entity string."""
        # Remove articles and common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = entity.strip().split()
        filtered_words = [w for w in words if w.lower() not in stop_words]
        return " ".join(filtered_words).title()
    
    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case for node IDs."""
        # Remove special characters and convert to lowercase
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', '_', text.strip())
        return text.lower()
    
    def _truncate_label(self, label: str) -> str:
        """Truncate label to 4 words max."""
        words = label.split()[:4]
        return " ".join(words)
    
    def _add_domain_relationships(self, entities: Set[str]) -> List[Tuple[str, str, str]]:
        """Add domain-specific relationships for quantum physics."""
        relationships = []
        entity_list = [self._to_snake_case(e) for e in entities]
        
        # Define some common quantum relationships
        quantum_relationships = [
            ("quantum_error_correction", "uses", "surface_code"),
            ("logical_qubit", "depends_on", "physical_qubit"),
            ("quantum_algorithm", "runs_on", "quantum_computer"),
            ("decoherence", "causes", "quantum_noise"),
            ("syndrome_measurement", "enables", "error_correction"),
            ("quantum_gate", "implements", "quantum_operation"),
            ("entanglement", "enables", "quantum_communication")
        ]
        
        for source, relation, target in quantum_relationships:
            if source in entity_list and target in entity_list:
                relationships.append((source, relation, target))
                
        return relationships
