<?php
session_start();

if(!isset($_SESSION["user_id"])) {
    header("Location: index.php");
    exit();
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>Resume Matcher</title>
</head>
<body>

<h2>Resume Matcher ✅</h2>
<p>Logged in as: <b><?php echo $_SESSION["email"]; ?></b></p>
<a href="logout.php">Logout</a>

<hr><br>

<form id="matchForm" enctype="multipart/form-data">
    <label><b>Job Description:</b></label><br>
    <textarea name="jd" id="jd" rows="8" cols="80" required></textarea><br><br>

    <label><b>Upload Resume (PDF):</b></label><br>
    <input type="file" name="resume" id="resume" accept="application/pdf" required><br><br>

    <button type="submit">Check Match</button>
</form>

<h3 id="score"></h3>
<pre id="output"></pre>

<script>
document.getElementById("matchForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    const jd = document.getElementById("jd").value;
    const resumeFile = document.getElementById("resume").files[0];

    const formData = new FormData();
    formData.append("jd", jd);
    formData.append("resume", resumeFile);

    try {
        const res = await fetch("http://127.0.0.1:5000/match", {
            method: "POST",
            body: formData
        });

        const data = await res.json();

        if(data.error) {
            document.getElementById("score").innerText = "❌ Error: " + data.error;
            return;
        }

        document.getElementById("score").innerText =
            "✅ Match Score: " + data.final_match_score + "%";

        document.getElementById("output").innerText =
            "Top Chunks:\n" + JSON.stringify(data.top_chunks, null, 2) +
            "\n\nFiltered Resume Text:\n" + data.filtered_resume_text;

    } catch (err) {
        document.getElementById("score").innerText =
            "❌ Flask Server Not Running / Network Error";
        console.log(err);
    }
});
</script>

</body>
</html>
