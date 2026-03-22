import asyncio

from backend.app.match_service import MatchRunService
from backend.tests.helpers import make_week_start, sample_embeddings, sample_personality


def test_match_worker_processes_pending_run(repository):
    async def setup():
        await repository.create_summary_job(
            job_id="job-1",
            user_id="user-1",
            source_filename="one.mp4",
            mime_type="video/mp4",
            duration_seconds=12.0,
        )
        await repository.create_summary_job(
            job_id="job-2",
            user_id="user-2",
            source_filename="two.mp4",
            mime_type="video/mp4",
            duration_seconds=12.0,
        )
        personality = sample_personality()
        weights = {
            "relational_orientation": personality.relational_orientation.weight,
            "creativity": personality.creativity.weight,
            "intellectualism": personality.intellectualism.weight,
            "humor": personality.humor.weight,
            "interests": personality.interests.weight,
            "cultural_identity": personality.cultural_identity.weight,
            "political_orientation": personality.political_orientation.weight,
        }
        await repository.insert_user_profile(
            user_id="user-1",
            job_id="job-1",
            profile_version=1,
            personality_json=personality,
            embeddings=sample_embeddings(1.0),
            weights=weights,
            composite_embedding=[0.0] * 5376,
        )
        await repository.insert_user_profile(
            user_id="user-2",
            job_id="job-2",
            profile_version=1,
            personality_json=personality,
            embeddings=sample_embeddings(2.0),
            weights=weights,
            composite_embedding=[0.0] * 5376,
        )
        await repository.trigger_match_run(make_week_start())

    asyncio.run(setup())

    service = MatchRunService(repository=repository, top_k=1)
    processed = asyncio.run(service.process_next_pending_run())

    assert processed is True
    run = next(iter(repository.match_runs.values()))
    assert run.status == "completed"
    assert run.user_count == 2
    rows = repository.match_rows_by_run[run.id]
    assert len(rows) == 2
    assert rows[0].user_id != rows[0].matched_user_id
    assert set(rows[0].score_breakdown.keys()) == {
        "relational_orientation",
        "creativity",
        "intellectualism",
        "humor",
        "interests",
        "cultural_identity",
        "political_orientation",
    }
