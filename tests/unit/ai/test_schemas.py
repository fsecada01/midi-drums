"""Tests for section-name case normalization in AI request schemas.

Regression coverage for a real crash hit via the REAPER panel's Riff-Lock
Beat tab: the Section field is free text (not a combo - see
midi_drums_panel.lua's combo_from_list rollout, which deliberately left
Section as an open field), so a title-cased value like "Intro" reached
PatternGenerationRequest's case-sensitive `Literal[...]` section field and
raised a pydantic ValidationError instead of generating a pattern.
"""

import pytest
from pydantic import ValidationError

from midi_drums.ai.schemas import AudioAnalysisRequest, PatternGenerationRequest


class TestPatternGenerationRequestSectionNormalization:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("Intro", "intro"),
            ("VERSE", "verse"),
            ("  Chorus  ", "chorus"),
            ("breakdown", "breakdown"),
        ],
    )
    def test_section_is_normalized(self, raw, expected):
        request = PatternGenerationRequest(
            description="aggressive metal breakdown with double bass",
            section=raw,
        )
        assert request.section == expected

    def test_unknown_section_still_rejected(self):
        with pytest.raises(ValidationError):
            PatternGenerationRequest(
                description="aggressive metal breakdown with double bass",
                section="Nonexistent",
            )

    def test_default_section_unaffected(self):
        request = PatternGenerationRequest(
            description="aggressive metal breakdown with double bass"
        )
        assert request.section == "verse"


class TestAudioAnalysisRequestTargetSectionNormalization:
    def test_target_section_is_normalized(self):
        request = AudioAnalysisRequest(
            audio_file_path="riff.wav", target_section="Outro"
        )
        assert request.target_section == "outro"

    def test_unknown_target_section_still_rejected(self):
        with pytest.raises(ValidationError):
            AudioAnalysisRequest(
                audio_file_path="riff.wav", target_section="Nonexistent"
            )
