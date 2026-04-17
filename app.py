from flask import Flask, render_template, request, send_file, jsonify
from personality_backend import generate_report_data
from question import questions
from playwright.sync_api import sync_playwright
import os
import uuid

app = Flask(__name__)

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html", questions=questions)


# ---------------- SUBMIT ----------------
@app.route("/submit", methods=["POST"])
def submit():
    try:
        # ---------------- 1. COLLECT ANSWERS ----------------
        answers = [
            request.form.get(f"answers_{i}")
            for i in range(1, len(questions) + 1)
        ]

        if None in answers or len(answers) != len(questions):
            return jsonify({"error": "All questions must be answered"}), 400

        print("✅ Answers:", answers)

        # ---------------- 2. AI PROCESSING ----------------
        try:
            report_data = generate_report_data(answers)
        except Exception as ai_error:
            print("❌ AI ERROR:", str(ai_error))
            return jsonify({"error": "AI processing failed"}), 500

        print("✅ AI Data keys:", report_data.keys())

        # ---------------- 3. RENDER HTML ----------------
        rendered_html = render_template(
            "master.html",
            data=report_data
        )

        # ---------------- 4. GENERATE PDF USING PLAYWRIGHT ----------------
        os.makedirs("output", exist_ok=True)

        html_filename = f"temp_{uuid.uuid4().hex}.html"
        html_path = os.path.join("output", html_filename)

        pdf_filename = f"report_{uuid.uuid4().hex}.pdf"
        pdf_path = os.path.join("output", pdf_filename)

        # Save HTML file
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        # Generate PDF using Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            page.goto(f"file:///{os.path.abspath(html_path)}")

            # Wait for full content load
            page.wait_for_load_state("networkidle")

            page.pdf(
                path=pdf_path,
                format="A4",
                print_background=True,
                prefer_css_page_size=True   
            )

            browser.close()

        print("✅ PDF Generated:", pdf_path)

        # ---------------- 5. RETURN FILE ----------------
        response = send_file(
            pdf_path,
            as_attachment=True,
            download_name="personality_report.pdf"
        )

        # ---------------- 6. AUTO CLEANUP ----------------
        @response.call_on_close
        def cleanup():
            try:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                if os.path.exists(html_path):
                    os.remove(html_path)
                print("🧹 Cleaned temp files")
            except Exception as e:
                print("Cleanup error:", str(e))

        return response

    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"error": "Something went wrong"}), 500


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
