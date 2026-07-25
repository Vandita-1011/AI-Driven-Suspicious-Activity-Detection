"""
Network Feature Extractor
=========================
Extracts graph-based features using the reference data and NetworkX.
"""
import pandas as pd
import networkx as nx

from src.data.dataset_context import DatasetContext
from src.constants.column_names import TxnCols, ComputedCols, RelationshipCols
from src.utils.logger import get_logger

logger = get_logger(__name__)


class NetworkFeatureExtractor:
    """
    Uses NetworkX to build relationship graphs and extract node-level features.
    """
    def __init__(self, context: DatasetContext) -> None:
        self.context = context

    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Appends network features to the DataFrame.
        """
        logger.debug("Extracting network features...")
        df = df.copy()

        # Build a basic graph from customer relationships if available
        G = nx.Graph()
        if not self.context.relationships.empty:
            edges = zip(
                self.context.relationships[RelationshipCols.CUSTOMER_ID_1],
                self.context.relationships[RelationshipCols.CUSTOMER_ID_2]
            )
            G.add_edges_from(edges)

        # Extract relationship count for each customer in the transactions dataframe
        if TxnCols.CUSTOMER_ID in df.columns:
            def get_degree(cust_id):
                return G.degree[cust_id] if G.has_node(cust_id) else 0
                
            df[ComputedCols.RELATIONSHIP_COUNT] = df[TxnCols.CUSTOMER_ID].apply(get_degree)

        return df
