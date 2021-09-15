import spacy

sample_inputs = [
    "I want to learn quantum mechanics",
    "I want to learn AI",
    "I want to study basic natural language processing",
    "I want to learn to code in c++",
    "I learn",
    "I want to learn AI and quantum mechanics",
    "I want to learn to write code in c++",
    "I want to learn about USC",
    "I am learning quantum mechanics",
    "I want to learn c++",
]

PATTERNS = ['dobj', 'conj', 'pobj']

class TopicExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_trf")


    def get_topic(self, query: str) -> str:
        doc = self.nlp(query)

        topics = []

        for chunk in doc.noun_chunks:
            if chunk.root.dep_ in PATTERNS:
                topics.append(chunk.text)

        return topics

if __name__ == '__main__':
    topic_extractor = TopicExtractor()
    for sample_input in sample_inputs:
        topics = topic_extractor.get_topic(sample_input)
        if len(topics) == 0:
            print(f'Could not extract a topic from the query: {sample_input}')
        else:
            print(f'Topic extracted from input "{sample_input}" -> "{topics}"')
