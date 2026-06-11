import pytest
from naturalization_layer.russian_lemmatizer import lemmatize_word, lemmatize_sentence
from naturalization_layer.rag_retriever import BM25Retriever

def test_russian_lemmatizer_basic():
    # Test noun declensions
    assert lemmatize_word("алгоритма") == "алгоритм"
    assert lemmatize_word("алгоритму") == "алгоритм"
    assert lemmatize_word("компьютерами") == "компьютер"
    
    # Test adjective declensions
    assert lemmatize_word("быстрому") == "быстрый"
    assert lemmatize_word("научного") == "научный"
    
    # Test verb conjugations
    assert lemmatize_word("работает") == "работать"
    assert lemmatize_word("разработали") == "разработать"

def test_lemmatize_sentence():
    sentence = "Этот метод был разработан для управления движением робота."
    lemmatized = lemmatize_sentence(sentence)
    
    # Check that words are lemmatized
    assert "метод" in lemmatized
    assert "разработать" in lemmatized
    assert "управление" in lemmatized
    assert "движение" in lemmatized
    assert "робот" in lemmatized

def test_bm25_retriever_inflection_matching():
    corpus = [
        {"text": "В диссертации предложен новый метод автоматического управления движением автомобиля.", "metadata": {"id": 1}},
        {"text": "Описание конструкции двигателя внутреннего сгорания.", "metadata": {"id": 2}}
    ]
    
    retriever = BM25Retriever(corpus)
    
    # Query with different inflections
    # "управлением автомобиля" -> inflected form of "управления движением автомобиля"
    query = "управлением автомобилем"
    
    results = retriever.retrieve(query, top_k=2)
    assert len(results) > 0
    assert results[0]["metadata"]["id"] == 1
    assert results[0]["score"] > 0.0
