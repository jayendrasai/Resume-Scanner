import { jsPDF } from "jspdf";
import { AnalysisData } from "../types";

export const generatePDFReport = (data: AnalysisData, filename: string) => {
    const doc = new jsPDF();
    const date = new Date().toLocaleDateString();

    // Header
    doc.setFont("helvetica", "bold");
    doc.setFontSize(22);
    doc.text("Resume Analysis Report", 20, 20);

    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(100, 100, 100);
    doc.text(`Generated on: ${date} | File: ${filename}`, 20, 28);

    // Score
    doc.setFontSize(16);
    doc.setTextColor(0, 0, 0);
    doc.text(`Match Score: ${data.match_score}%`, 20, 45);

    // Missing Keywords
    doc.setFontSize(14);
    doc.setFont("helvetica", "bold");
    doc.text("Missing Keywords:", 20, 60);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(12);
    let yPos = 70;
    data.missing_keywords.forEach((kw) => {
        doc.text(`• ${kw}`, 25, yPos);
        yPos += 8;
    });

    // Tips
    yPos += 10;
    doc.setFontSize(14);
    doc.setFont("helvetica", "bold");
    doc.text("Improvement Tips:", 20, yPos);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(11);
    yPos += 10;
    data.tips.forEach((tip, idx) => {
        // Split text so it wraps properly in the PDF
        const lines = doc.splitTextToSize(`${idx + 1}. ${tip}`, 170);
        doc.text(lines, 20, yPos);
        yPos += (lines.length * 7) + 4;
    });

    doc.save(`Analysis_${filename}.pdf`);
};