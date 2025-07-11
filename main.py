from datetime import datetime

import sqlite3

from sqlite3 import Connection

from fastapi import FastAPI, Depends, status
from typing import Literal, Annotated


app = FastAPI()


DB_NAME = 'reviews.db'

REVIEWS_DICT = {
    'хорош': 'positive',
    'люблю': 'positive',
    'ненавиж': 'negative',
    'плохо': 'negative',
}


def get_session():
    """Отвечает за поддержания соединения с бд"""
    with sqlite3.connect(DB_NAME) as session:
        yield session


def init_db():
    with sqlite3.connect(DB_NAME) as session:
        session.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              text TEXT NOT NULL,
              sentiment TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
        """)


def add_review(session: Connection, text: str) -> dict:
    """Добавляет отзыв по тексту в бд"""
    # deprecated datetime.utcnow(). Я бы заменил на datetime.now(timezone.utc)
    created_at = datetime.utcnow().isoformat()
    sentiment = REVIEWS_DICT.get(text, 'neutral')
    sql_expression = 'INSERT INTO reviews(text, sentiment, created_at) VALUES (?, ?, ?) RETURNING id'
    result_from_db = session.execute(sql_expression, (text, sentiment, created_at))
    id_ = result_from_db.fetchone()[0]
    return {
        'id': id_,
        'created_at': created_at,
        'text': text,
        'sentiment': sentiment
    }


def fetch_reviews(session: Connection, sentiment: str) -> list[dict]:
    """Возвращает список отзывов по заданному настроению"""
    sql_expression = 'SELECT id, text, sentiment, created_at FROM reviews WHERE sentiment = ?'
    result_from_db = session.execute(sql_expression, (sentiment,))
    return [{
        'id': id_,
        'text': text,
        'sentiment': sentiment,
        'created_at': created_at,
    }
    for id_, text, sentiment, created_at in result_from_db.fetchall()]


@app.get('/reviews', status_code=status.HTTP_200_OK)
def get_reviews(
    session: Annotated[Connection, Depends(get_session)],
    sentiment: Literal['negative']
) -> list[dict]:
    """Выводит отзывы по заданному настроению sentiment"""
    return fetch_reviews(session, sentiment)


@app.post('/reviews', status_code=status.HTTP_201_CREATED)
def post_review(
    session: Annotated[Connection, Depends(get_session)],
    text: str,
) -> dict:
    """Добавляет отзыв по заданному тексту"""
    return add_review(session, text)


init_db()
