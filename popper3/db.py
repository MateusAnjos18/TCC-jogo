from __future__ import annotations

import sqlite3
import os
from dataclasses import dataclass
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("LOCALAPPDATA", APP_DIR)) / "Popper 3" / "data"
DB_PATH = DATA_DIR / "popper3.db"


@dataclass
class Deck:
    id: int
    name: str
    cover_path: str | None


@dataclass
class Card:
    id: int
    deck_id: int
    card_type: str
    title: str
    description: str
    score: int | None
    truth: int | None
    splash_path: str | None


class Database:
    def __init__(self, path: Path = DB_PATH) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.migrate()

    def migrate(self) -> None:
        self.conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                cover_path TEXT
            );

            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_id INTEGER NOT NULL,
                card_type TEXT NOT NULL CHECK(card_type IN ('game', 'player')),
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                score INTEGER,
                truth INTEGER,
                splash_path TEXT,
                FOREIGN KEY(deck_id) REFERENCES decks(id) ON DELETE CASCADE
            );
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def decks(self) -> list[Deck]:
        rows = self.conn.execute("SELECT * FROM decks ORDER BY name COLLATE NOCASE").fetchall()
        return [Deck(row["id"], row["name"], row["cover_path"]) for row in rows]

    def deck(self, deck_id: int) -> Deck | None:
        row = self.conn.execute("SELECT * FROM decks WHERE id = ?", (deck_id,)).fetchone()
        if row is None:
            return None
        return Deck(row["id"], row["name"], row["cover_path"])

    def create_deck(self, name: str, cover_path: str | None) -> int:
        cur = self.conn.execute("INSERT INTO decks(name, cover_path) VALUES(?, ?)", (name, cover_path))
        self.conn.commit()
        return int(cur.lastrowid)

    def update_deck(self, deck_id: int, name: str, cover_path: str | None) -> None:
        self.conn.execute("UPDATE decks SET name = ?, cover_path = ? WHERE id = ?", (name, cover_path, deck_id))
        self.conn.commit()

    def delete_deck(self, deck_id: int) -> None:
        self.conn.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
        self.conn.commit()

    def cards(self, deck_id: int) -> list[Card]:
        rows = self.conn.execute(
            "SELECT * FROM cards WHERE deck_id = ? ORDER BY id DESC",
            (deck_id,),
        ).fetchall()
        return [self._card(row) for row in rows]

    def card(self, card_id: int) -> Card | None:
        row = self.conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
        return self._card(row) if row else None

    def create_card(
        self,
        deck_id: int,
        card_type: str,
        title: str,
        description: str,
        score: int | None,
        truth: int | None,
        splash_path: str | None,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO cards(deck_id, card_type, title, description, score, truth, splash_path)
            VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (deck_id, card_type, title, description, score, truth, splash_path),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_card(
        self,
        card_id: int,
        card_type: str,
        title: str,
        description: str,
        score: int | None,
        truth: int | None,
        splash_path: str | None,
    ) -> None:
        self.conn.execute(
            """
            UPDATE cards
            SET card_type = ?, title = ?, description = ?, score = ?, truth = ?, splash_path = ?
            WHERE id = ?
            """,
            (card_type, title, description, score, truth, splash_path, card_id),
        )
        self.conn.commit()

    def delete_card(self, card_id: int) -> None:
        self.conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        self.conn.commit()

    def import_game_cards(self, deck_id: int, cards: list[dict[str, object]]) -> int:
        for card in cards:
            self.create_card(
                deck_id=deck_id,
                card_type="game",
                title=str(card["title"]),
                description=str(card.get("description", "")),
                score=int(card.get("score") or 0),
                truth=1 if card.get("truth") else 0,
                splash_path=None,
            )
        return len(cards)

    @staticmethod
    def _card(row: sqlite3.Row) -> Card:
        return Card(
            id=row["id"],
            deck_id=row["deck_id"],
            card_type=row["card_type"],
            title=row["title"],
            description=row["description"],
            score=row["score"],
            truth=row["truth"],
            splash_path=row["splash_path"],
        )
