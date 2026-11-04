import threading
import time

import pytest

from app.services.locks import PatientLocks


def _peak_concurrency(uhids: list[str]) -> int:
    locks = PatientLocks()
    state = {"active": 0, "peak": 0}

    def critical_section(uhid: str) -> None:
        with locks.hold(uhid):
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
            time.sleep(0.05)
            state["active"] -= 1

    threads = [threading.Thread(target=critical_section, args=(uhid,)) for uhid in uhids]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return state["peak"]


def test_same_patient_is_serialised() -> None:
    assert _peak_concurrency(["MG1"] * 4) == 1


def test_different_patients_run_in_parallel() -> None:
    assert _peak_concurrency(["MG1", "MG2", "MG3"]) > 1


def test_lock_is_released_after_an_exception() -> None:
    locks = PatientLocks()

    with pytest.raises(RuntimeError), locks.hold("MG1"):
        raise RuntimeError("boom")

    with locks.hold("MG1"):
        pass
