package com.resumeoptimizer.tools;

import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.apache.poi.xwpf.usermodel.XWPFParagraph;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Document parsing tools — FunctionTool targets for the DocumentParserAgent.
 * Replaces Python's document_parser/tools.py using Apache PDFBox and Apache POI.
 */
public final class DocumentParserTools {

    private static final Logger logger = LoggerFactory.getLogger(DocumentParserTools.class);

    private DocumentParserTools() {}

    /**
     * Parse a resume file from a local file path.
     * Supports PDF, DOCX, and TXT files.
     *
     * @param filePath Full absolute path to the resume file.
     * @return Map with keys: success (boolean), text (String), error (String|null)
     */
    public static Map<String, Object> parseResumeFile(String filePath) {
        if (filePath == null || filePath.isBlank()) {
            return error("No file path provided.");
        }

        filePath = filePath.strip().replace("\"", "").replace("'", "");
        File file = new File(filePath);

        if (!file.exists()) {
            return error("File not found: " + filePath);
        }

        String ext = filePath.substring(filePath.lastIndexOf('.')).toLowerCase();
        byte[] fileBytes;
        try {
            fileBytes = Files.readAllBytes(file.toPath());
        } catch (IOException e) {
            return error("Could not read file: " + e.getMessage());
        }

        return switch (ext) {
            case ".pdf" -> parsePdf(fileBytes);
            case ".docx" -> parseDocx(fileBytes);
            case ".txt" -> parsePlainText(new String(fileBytes));
            default -> error("Unsupported file type: " + ext + ". Use .pdf, .docx, or .txt");
        };
    }

    /**
     * Extract text from PDF bytes using Apache PDFBox with page-boundary markers.
     */
    public static Map<String, Object> parsePdf(byte[] fileBytes) {
        if (fileBytes == null || fileBytes.length == 0) {
            return error("PDF bytes are empty");
        }

        try (PDDocument document = Loader.loadPDF(fileBytes)) {
            int totalPages = document.getNumberOfPages();
            StringBuilder textBuilder = new StringBuilder();

            PDFTextStripper stripper = new PDFTextStripper();
            for (int i = 1; i <= totalPages; i++) {
                stripper.setStartPage(i);
                stripper.setEndPage(i);
                String pageText = stripper.getText(document);
                if (pageText != null && !pageText.isBlank()) {
                    textBuilder.append(pageText.strip());
                    // Inject page-boundary markers for multi-page resumes
                    if (totalPages > 1 && i < totalPages) {
                        textBuilder.append("\n--- PAGE ").append(i)
                                .append(" OF ").append(totalPages).append(" ---\n");
                    }
                }
            }

            String fullText = textBuilder.toString().strip();
            if (fullText.isEmpty()) {
                return error("PDF appears to be empty or image-only. Try converting to DOCX first.");
            }
            return success(fullText);

        } catch (IOException e) {
            return error("PDF parsing failed: " + e.getMessage());
        }
    }

    /**
     * Extract text from DOCX bytes using Apache POI.
     */
    public static Map<String, Object> parseDocx(byte[] fileBytes) {
        if (fileBytes == null || fileBytes.length == 0) {
            return error("DOCX bytes are empty");
        }

        try (XWPFDocument document = new XWPFDocument(new ByteArrayInputStream(fileBytes))) {
            StringBuilder textBuilder = new StringBuilder();
            for (XWPFParagraph paragraph : document.getParagraphs()) {
                String text = paragraph.getText();
                if (text != null && !text.isBlank()) {
                    textBuilder.append(text.strip()).append("\n");
                }
            }

            String fullText = textBuilder.toString().strip();
            if (fullText.isEmpty()) {
                return error("DOCX appears to be empty.");
            }
            return success(fullText);

        } catch (IOException e) {
            return error("DOCX parsing failed: " + e.getMessage());
        }
    }

    /**
     * Process plain text resume content (passthrough with cleanup).
     */
    public static Map<String, Object> parsePlainText(String text) {
        if (text == null || text.isBlank()) {
            return error("Provided text is empty.");
        }
        return success(text.strip());
    }

    private static Map<String, Object> success(String text) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("success", true);
        result.put("text", text);
        result.put("error", null);
        return result;
    }

    private static Map<String, Object> error(String message) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("success", false);
        result.put("text", "");
        result.put("error", message);
        return result;
    }
}
