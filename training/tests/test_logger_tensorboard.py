import json
import tempfile
from pathlib import Path

import pytest

from training.curriculum.logger import TrainingLogger


@pytest.fixture
def tmp_log_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def _log_one_update(logger: TrainingLogger) -> None:
    logger.start_training()
    logger.start_phase(phase_number=1, team_sizes=[1], episodes=10)
    logger.log_episode(
        1,
        {"winner": "team_a", "steps": 30, "total_reward": {"a": 1.0}},
    )
    logger.log_update(
        {
            "policy_loss": -0.01,
            "value_loss": 50.0,
            "entropy": 2.0,
            "entropy_coeff": 0.05,
        }
    )


def _log_one_eval(logger: TrainingLogger) -> None:
    logger.log_eval(
        {
            "n_episodes": 20,
            "team_size": 1,
            "win_rate": 0.75,
            "loss_rate": 0.25,
            "draw_rate": 0.0,
            "avg_steps": 50.0,
        }
    )


class TestTensorBoardFlag:
    def test_tensorboard_disabled_creates_no_dir(self, tmp_log_dir):
        logger = TrainingLogger(log_dir=tmp_log_dir, enable_tensorboard=False)
        _log_one_update(logger)
        assert not (Path(tmp_log_dir) / "tb").exists()

    def test_tensorboard_enabled_creates_event_file(self, tmp_log_dir):
        logger = TrainingLogger(log_dir=tmp_log_dir, enable_tensorboard=True)
        _log_one_update(logger)
        _log_one_eval(logger)
        logger.end_training()

        tb_dir = Path(tmp_log_dir) / "tb"
        assert tb_dir.exists()
        events = list(tb_dir.glob("events.out.tfevents.*"))
        assert len(events) >= 1


class TestJSONLBackwardCompat:
    def test_jsonl_unchanged_with_tensorboard_disabled(self, tmp_log_dir):
        logger = TrainingLogger(log_dir=tmp_log_dir, enable_tensorboard=False)
        _log_one_update(logger)
        _log_one_eval(logger)

        log_file = Path(tmp_log_dir) / "training.jsonl"
        assert log_file.exists()
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2

        update_record = json.loads(lines[0])
        eval_record = json.loads(lines[1])

        assert "policy_loss" in update_record
        assert "value_loss" in update_record
        assert "entropy" in update_record
        assert "entropy_coeff" in update_record
        assert "eval" in eval_record
        assert eval_record["eval"]["win_rate"] == 0.75

    def test_jsonl_unchanged_with_tensorboard_enabled(self, tmp_log_dir):
        logger = TrainingLogger(log_dir=tmp_log_dir, enable_tensorboard=True)
        _log_one_update(logger)
        _log_one_eval(logger)
        logger.end_training()

        log_file = Path(tmp_log_dir) / "training.jsonl"
        assert log_file.exists()
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2

        update_record = json.loads(lines[0])
        eval_record = json.loads(lines[1])

        assert "policy_loss" in update_record
        assert "value_loss" in update_record
        assert "entropy" in update_record
        assert "entropy_coeff" in update_record
        assert "eval" in eval_record
        assert eval_record["eval"]["win_rate"] == 0.75


class TestEndTrainingSafety:
    def test_end_training_closes_writer_safely(self, tmp_log_dir):
        logger = TrainingLogger(log_dir=tmp_log_dir, enable_tensorboard=True)
        logger.start_training()
        logger.end_training()

    def test_end_training_safe_with_tensorboard_disabled(self, tmp_log_dir):
        logger = TrainingLogger(log_dir=tmp_log_dir, enable_tensorboard=False)
        logger.start_training()
        logger.end_training()


class TestDefaultBehavior:
    def test_default_enables_tensorboard(self, tmp_log_dir):
        logger = TrainingLogger(log_dir=tmp_log_dir)
        _log_one_update(logger)
        logger.end_training()

        tb_dir = Path(tmp_log_dir) / "tb"
        assert tb_dir.exists()
