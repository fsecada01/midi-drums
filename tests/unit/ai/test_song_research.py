"""Tests for the song_research spike (see midi_drums/ai/song_research.py).

All network access is mocked via monkeypatch on the module's internal
``_rate_limited_get`` — these tests must never hit the real MusicBrainz/
AcousticBrainz APIs, matching this repo's convention of deterministic,
offline unit tests.
"""

from midi_drums.ai import song_research


class TestResearchSongFullMatch:
    def test_combines_musicbrainz_and_acousticbrainz_facts(self, monkeypatch):
        responses = {
            "recording/?query=": {"recordings": [{"id": "mbid-123"}]},
            "recording/mbid-123?": {
                "artist-credit": [{"name": "Black Sabbath"}],
                "releases": [{"date": "1970-02-13"}, {"date": "1970-06-01"}],
                "genres": [{"name": "heavy metal"}, {"name": "doom metal"}],
                "relations": [
                    {
                        "type": "instrument",
                        "attributes": ["drums"],
                        "artist": {"name": "Bill Ward"},
                    },
                    {
                        "type": "vocal",
                        "attributes": ["lead vocals"],
                        "artist": {"name": "Ozzy Osbourne"},
                    },
                ],
            },
            "acousticbrainz.org/api/v1/mbid-123/low-level": {
                "rhythm": {"bpm": 79.3},
                "tonal": {"key_key": "E", "key_scale": "minor"},
            },
        }

        def fake_get(url, timeout=8.0):
            for fragment, payload in responses.items():
                if fragment in url:
                    return payload
            raise AssertionError(f"unexpected URL in test: {url}")

        monkeypatch.setattr(song_research, "_rate_limited_get", fake_get)

        facts = song_research.research_song("Black Sabbath", "Black Sabbath")

        assert facts.mbid == "mbid-123"
        assert facts.artist == "Black Sabbath"
        assert facts.first_release_date == "1970-02-13"
        assert facts.genres == ["doom metal", "heavy metal"]
        assert facts.drummer_personnel == ["Bill Ward"]
        assert facts.tempo_bpm == 79.3
        assert facts.musical_key == "E minor"
        assert "musicbrainz.org/recording/mbid-123" in facts.sources[0]
        assert any("acousticbrainz.org" in s for s in facts.sources)

    def test_fact_sheet_renders_verified_facts(self, monkeypatch):
        monkeypatch.setattr(
            song_research,
            "_rate_limited_get",
            lambda url, timeout=8.0: (
                {"recordings": [{"id": "mbid-1"}]}
                if "query=" in url
                else (
                    {
                        "artist-credit": [{"name": "Rush"}],
                        "releases": [{"date": "1981-02-12"}],
                        "genres": [{"name": "progressive rock"}],
                        "relations": [],
                    }
                    if "recording/mbid-1?" in url
                    else {"rhythm": {"bpm": 155.0}, "tonal": {}}
                )
            ),
        )

        facts = song_research.research_song("Tom Sawyer", "Rush")
        sheet = facts.as_prompt_fact_sheet()

        assert "VERIFIED SONG FACTS for 'Tom Sawyer' by Rush" in sheet
        assert "Release date: 1981-02-12" in sheet
        assert "Genre tags: progressive rock" in sheet
        assert "Tempo: 155 BPM" in sheet
        assert "Sources:" in sheet


class TestPickBestCandidate:
    """Regression coverage for a bug found via live testing: MusicBrainz's
    title+artist search for a real song ("Headless Cross" by Black
    Sabbath) returned several tied-score candidates, and the naive top-1
    result was a 2018 fan-recorded live bootleg rather than the 1989
    studio track — even though a candidate with an "Official"/"Promotion"
    release was present a few entries down.
    """

    def test_prefers_candidate_with_earliest_official_release(self):
        bootleg_2018 = {
            "id": "bootleg-mbid",
            "releases": [{"date": "2018", "status": "Bootleg"}],
        }
        bootleg_2015 = {
            "id": "bootleg-2015-mbid",
            "releases": [{"date": "2015", "status": "Bootleg"}],
        }
        studio_1989 = {
            "id": "studio-mbid",
            "releases": [
                {"date": "1989", "status": "Promotion"},
                {"date": "2001-04-02", "status": "Official"},
            ],
        }

        winner = song_research._pick_best_candidate(
            [bootleg_2018, bootleg_2015, studio_1989]
        )

        assert winner["id"] == "studio-mbid"

    def test_falls_back_to_top1_when_only_bootlegs_indexed(self):
        only_bootleg = {
            "id": "only-bootleg-mbid",
            "releases": [{"date": "2020", "status": "Bootleg"}],
        }
        no_releases = {"id": "no-releases-mbid", "releases": []}

        winner = song_research._pick_best_candidate([only_bootleg, no_releases])

        assert winner["id"] == "only-bootleg-mbid"


class TestResearchSongLookupMiss:
    def test_no_musicbrainz_match_returns_minimal_facts(self, monkeypatch):
        monkeypatch.setattr(
            song_research, "_rate_limited_get", lambda url, timeout=8.0: None
        )

        facts = song_research.research_song("Some Obscure Song", "Nobody")

        assert facts.title == "Some Obscure Song"
        assert facts.artist == "Nobody"
        assert facts.mbid is None
        assert facts.genres == []
        assert facts.sources == []

    def test_lookup_miss_fact_sheet_says_so(self, monkeypatch):
        monkeypatch.setattr(
            song_research, "_rate_limited_get", lambda url, timeout=8.0: None
        )

        facts = song_research.research_song("Some Obscure Song")
        sheet = facts.as_prompt_fact_sheet()

        assert "no verified facts found" in sheet
        assert "Sources:" not in sheet

    def test_network_error_never_raises(self, monkeypatch):
        # Exercise the real _rate_limited_get (not a monkeypatched stand-in)
        # to prove it actually catches urllib errors rather than propagating.
        def fake_urlopen(*args, **kwargs):
            raise song_research.urllib.error.URLError("network down")

        monkeypatch.setattr(
            song_research.urllib.request, "urlopen", fake_urlopen
        )

        facts = song_research.research_song("Anything")
        assert facts.mbid is None
