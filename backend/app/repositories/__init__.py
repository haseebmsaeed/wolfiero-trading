"""Data repositories for Firestore-backed storage.

The repository pattern provides a thin abstraction over Firestore, allowing services
to be tested with fake in-memory implementations without touching the database or emulator.

All repositories implement Protocol interfaces defined in protocols.py, ensuring
type safety and enabling easy mock implementations for unit tests.
"""
