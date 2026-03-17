import csv

class ReportExporter:

    def export_csv(self, filename, score, complexity, long_functions):
        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Score", "Complexity", "Long Functions"])
            writer.writerow([score, complexity, ", ".join(long_functions)])