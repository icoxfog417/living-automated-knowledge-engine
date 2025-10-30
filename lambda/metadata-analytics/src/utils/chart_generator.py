"""Chart generator for metadata analytics."""

import logging
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

# Use non-interactive backend for Lambda environment
matplotlib.use("Agg")

logger = logging.getLogger(__name__)

# Set seaborn style
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["font.size"] = 10


@dataclass
class ChartResult:
    """Result of chart generation."""

    chart_type: str  # 'bar'
    title: str
    file_path: str
    metadata_key: str  # Which metadata field this chart represents
    description: str


@dataclass
class TableData:
    """Data for table display instead of chart."""

    metadata_key: str
    title: str
    data: Dict[str, int]  # value -> count
    reason: str  # Why table was chosen over chart


class ChartGenerator:
    """Generate charts from metadata aggregation."""

    # Thresholds for determining chart vs table display
    MAX_LABEL_LENGTH = 80  # Average label length threshold
    MAX_CATEGORIES_FOR_CHART = 15  # Maximum categories for chart display

    def __init__(self):
        """Initialize chart generator."""
        self.color_palette = sns.color_palette("husl", 10)

    def generate_charts(
        self, aggregation: Dict[str, Any]
    ) -> Tuple[List[ChartResult], List[TableData]]:
        """Generate charts and table data from aggregation.

        Args:
            aggregation: Aggregated metadata statistics

        Returns:
            Tuple of (chart results, table data)
        """
        logger.info("Starting deterministic chart and table generation...")
        charts = []
        tables = []

        # Get schema and aggregations
        schema = aggregation.get("schema", {})
        aggs = aggregation.get("aggregations", {})
        by_file_type = aggregation.get("by_file_type", {})

        # 1. File type distribution (always as chart)
        if by_file_type:
            chart = self._generate_file_type_chart(by_file_type)
            if chart:
                charts.append(chart)

        # 2. Process each metadata field
        for key, key_info in schema.items():
            if key not in aggs:
                continue

            agg_data = aggs[key]

            # Skip numeric fields
            if key_info.get("is_numeric", False):
                continue

            # Decide between chart and table
            if self._should_use_table(key, agg_data):
                table = self._create_table_data(key, agg_data, key_info)
                if table:
                    tables.append(table)
            else:
                chart = self._generate_bar_chart(key, agg_data, key_info)
                if chart:
                    charts.append(chart)

        logger.info(f"Generated {len(charts)} charts and {len(tables)} tables")
        return charts, tables

    def _should_use_table(self, key: str, data: Dict[str, int]) -> bool:
        """Determine if table display is more appropriate than chart.

        Args:
            key: Metadata key name
            data: Dictionary of value to count

        Returns:
            True if table should be used, False for chart
        """
        if not data:
            return False

        # Remove '_others' for analysis
        chart_data = {k: v for k, v in data.items() if k != "_others"}
        if not chart_data:
            return False

        # Check category count
        if len(chart_data) > self.MAX_CATEGORIES_FOR_CHART:
            logger.info(f"Using table for {key}: too many categories ({len(chart_data)})")
            return True

        # Check average label length
        avg_length = sum(len(str(k)) for k in chart_data.keys()) / len(chart_data)
        if avg_length > self.MAX_LABEL_LENGTH:
            logger.info(f"Using table for {key}: labels too long (avg {avg_length:.1f} chars)")
            return True

        return False

    def _create_table_data(
        self, key: str, data: Dict[str, int], key_info: Dict[str, Any]
    ) -> TableData:
        """Create table data for fields with long text or many categories.

        Args:
            key: Metadata key name
            data: Dictionary of value to count
            key_info: Schema information

        Returns:
            TableData object
        """
        try:
            # Remove '_others' if present
            table_data = {k: v for k, v in data.items() if k != "_others"}

            if not table_data:
                return None

            title = key.replace("_", " ").title()
            occurrence_rate = key_info.get("occurrence_rate", 0)

            # Determine reason
            avg_length = sum(len(str(k)) for k in table_data.keys()) / len(table_data)
            if avg_length > self.MAX_LABEL_LENGTH:
                reason = f"Long text (avg {avg_length:.0f} chars)"
            elif len(table_data) > self.MAX_CATEGORIES_FOR_CHART:
                reason = f"Many categories ({len(table_data)})"
            else:
                reason = "Complex data"

            return TableData(
                metadata_key=key,
                title=f"{title} Distribution",
                data=table_data,
                reason=reason,
            )

        except Exception as e:
            logger.error(f"Error creating table data for {key}: {e}", exc_info=True)
            return None

    def _generate_file_type_chart(self, data: Dict[str, int]) -> ChartResult:
        """Generate file type distribution chart.

        Args:
            data: Dictionary of file extension to count

        Returns:
            ChartResult with chart information
        """
        try:
            # Sort by count descending
            sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
            extensions = [ext or "unknown" for ext, _ in sorted_data[:10]]
            counts = [count for _, count in sorted_data[:10]]

            # Create bar chart
            fig, ax = plt.subplots(figsize=(12, 6))
            bars = ax.bar(extensions, counts, color=self.color_palette)

            # Customize chart
            ax.set_xlabel("File Extension", fontsize=12, fontweight="bold")
            ax.set_ylabel("Count", fontsize=12, fontweight="bold")
            ax.set_title("File Type Distribution", fontsize=14, fontweight="bold", pad=20)
            ax.grid(axis="y", alpha=0.3)

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    f"{int(height)}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False)
            file_path = temp_file.name
            temp_file.close()

            plt.savefig(file_path, dpi=150, bbox_inches="tight")
            plt.close()

            total = sum(counts)
            description = f"Distribution of {total} files across {len(extensions)} file types"

            return ChartResult(
                chart_type="bar",
                title="File Type Distribution",
                file_path=file_path,
                metadata_key="file_type",
                description=description,
            )

        except Exception as e:
            logger.error(f"Error generating file type chart: {e}", exc_info=True)
            return None

    def _generate_bar_chart(
        self, key: str, data: Dict[str, int], key_info: Dict[str, Any]
    ) -> ChartResult:
        """Generate horizontal bar chart for categorical data.

        Args:
            key: Metadata key name
            data: Dictionary of value to count
            key_info: Schema information

        Returns:
            ChartResult with chart information
        """
        try:
            # Remove '_others' if present
            chart_data = {k: v for k, v in data.items() if k != "_others"}

            if not chart_data:
                return None

            # Sort by count descending and limit to top 10
            sorted_data = sorted(chart_data.items(), key=lambda x: x[1], reverse=True)
            sorted_data = sorted_data[:10]
            labels = [str(label) for label, _ in sorted_data]
            values = [count for _, count in sorted_data]

            # Create horizontal bar chart
            fig, ax = plt.subplots(figsize=(12, max(6, len(labels) * 0.5)))
            bars = ax.barh(labels, values, color=self.color_palette)

            # Customize chart
            title = key.replace("_", " ").title()
            ax.set_xlabel("Count", fontsize=12, fontweight="bold")
            ax.set_ylabel(title, fontsize=12, fontweight="bold")
            ax.set_title(f"{title} Distribution", fontsize=14, fontweight="bold", pad=20)
            ax.grid(axis="x", alpha=0.3)

            # Add value labels on bars
            for bar in bars:
                width = bar.get_width()
                ax.text(
                    width,
                    bar.get_y() + bar.get_height() / 2.0,
                    f" {int(width)}",
                    ha="left",
                    va="center",
                    fontsize=9,
                )

            plt.tight_layout()

            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False)
            file_path = temp_file.name
            temp_file.close()

            plt.savefig(file_path, dpi=150, bbox_inches="tight")
            plt.close()

            total = sum(values)
            occurrence_rate = key_info.get("occurrence_rate", 0)
            description = (
                f"Distribution of {key} across {len(labels)} categories "
                f"(total: {total}, occurrence rate: {occurrence_rate}%)"
            )

            return ChartResult(
                chart_type="bar",
                title=f"{title} Distribution",
                file_path=file_path,
                metadata_key=key,
                description=description,
            )

        except Exception as e:
            logger.error(f"Error generating bar chart for {key}: {e}", exc_info=True)
            return None
