# prompt_builder.py

from pathlib import Path
from type_behavior import (
    get_type_behavior,
    should_generate_toc,
    get_tone,
    get_forbidden_phrases
)
from section_rules import get_section_rules, get_section_word_limit
from risk_behavior import get_risk_behavior


class SectionPromptBuilder:
    """
    Assembles the complete prompt for a single section.
    Uses all behavior files to create the strongest possible prompt.
    """

    def __init__(self):
        self.template_path = Path(__file__).parent / "section_prompt.txt"
        self.template = self.template_path.read_text()

    def build(
        self,
        document_name: str,
        document_type: str,
        section_name: str,
        mandatory: bool,
        risk_level: str,
        company_profile: dict,
        document_inputs: dict,
        industry_context: str,
        all_sections: list
    ) -> str:
        """
        Build the complete prompt for section generation.
        """

        # Get behavior components
        type_behavior_data = get_type_behavior(document_type)
        type_behavior_str = type_behavior_data.get("rules", "")
        tone = type_behavior_data.get("tone", "professional")
        voice = type_behavior_data.get("voice", "third-person")
        format_style = type_behavior_data.get("format", "structured headings")

        section_rules_str = get_section_rules(document_type, section_name)
        risk_behavior_str = get_risk_behavior(risk_level)
        toc_required = should_generate_toc(document_type)
        forbidden = get_forbidden_phrases(document_type)
        min_words, max_words = get_section_word_limit(document_type, section_name)

        # Format company profile
        company_profile_str = self._format_company_profile(company_profile)

        # Format document inputs
        document_inputs_str = self._format_document_inputs(document_inputs)

        # Format all sections list for TOC
        all_sections_str = self._format_sections_list(all_sections)

        # Format forbidden phrases
        forbidden_str = ", ".join(f'"{p}"' for p in forbidden) if forbidden else "None"

        # Build prompt
        prompt = self.template.format(
            document_name=document_name,
            document_type=document_type,
            section_name=section_name,
            mandatory=str(mandatory),
            risk_level=risk_level,
            company_profile=company_profile_str,
            document_inputs=document_inputs_str,
            industry_context=industry_context,
            tone=tone,
            voice=voice,
            format_style=format_style,
            type_behavior=type_behavior_str,
            section_rules=section_rules_str,
            risk_behavior=risk_behavior_str,
            toc_required=str(toc_required).upper(),
            all_sections=all_sections_str,
            min_words=min_words,
            max_words=max_words,
            company_name=company_profile.get("company_name", "[Company]"),
            forbidden_phrases=forbidden_str
        )

        return prompt

    def _format_company_profile(self, profile: dict) -> str:
        lines = []
        field_map = {
            "company_name": "Company Name",
            "industry": "Industry",
            "employee_count": "Employee Count",
            "region": "Region",
            "compliance_frameworks": "Compliance Frameworks"
        }
        for key, label in field_map.items():
            value = profile.get(key)
            if value:
                if isinstance(value, list):
                    value = ", ".join(value)
                lines.append(f"{label}: {value}")
        return "\n".join(lines)

    def _format_document_inputs(self, inputs: dict) -> str:
        if not inputs:
            return "No additional inputs provided."
        lines = []
        for question, answer in inputs.items():
            lines.append(f"Q: {question}")
            if isinstance(answer, list):
                lines.append("A: " + ", ".join(str(a) for a in answer))
            else:
                lines.append(f"A: {answer}")
            lines.append("")
        return "\n".join(lines)

    def _format_sections_list(self, sections: list) -> str:
        if not sections:
            return "Sections not provided"
        return "\n".join(
            f"{i+1}. {s.get('name', s) if isinstance(s, dict) else s}"
            for i, s in enumerate(sections)
        )