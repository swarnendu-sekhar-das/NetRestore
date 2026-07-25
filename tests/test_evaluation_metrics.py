import unittest

from src.evaluation.evaluate import calculate_document_retrieval_metrics


class DocumentRetrievalMetricsTests(unittest.TestCase):
    def test_exact_document_ranking_metrics(self):
        metrics = calculate_document_retrieval_metrics(
            [
                ["expected-a.pdf", "other.pdf"],
                ["other.pdf", "expected-b.pdf", "third.pdf"],
                ["other.pdf", "third.pdf", "expected-c.pdf"],
                ["other.pdf"],
            ],
            ["expected-a.pdf", "expected-b.pdf", "expected-c.pdf", "expected-d.pdf"],
        )

        self.assertEqual(metrics["total_queries"], 4)
        self.assertEqual(metrics["exact_document_hit_at_1"], 0.25)
        self.assertEqual(metrics["exact_document_recall_at_3"], 0.75)
        self.assertAlmostEqual(metrics["mrr"], (1 + 0.5 + (1 / 3)) / 4)

    def test_metric_inputs_must_have_matching_lengths(self):
        with self.assertRaises(ValueError):
            calculate_document_retrieval_metrics([["a.pdf"]], ["a.pdf", "b.pdf"])
