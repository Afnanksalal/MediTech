document.addEventListener("DOMContentLoaded", () => {
  const startButton = document.getElementById("startRecord");
  const stopButton = document.getElementById("stopRecord");
  const statusElement = document.getElementById("status");
  const transcriptionElement = document.getElementById("transcription");
  const translationElement = document.getElementById("translation");
  const emrDataElement = document.getElementById("emr-data");
  const suggestionsElement = document.getElementById("suggestions");
  const resultsElement = document.getElementById("results");
  const loadingElement = document.createElement("div");
  loadingElement.id = "loading-spinner";
  const downloadReportButton = document.getElementById("downloadReport");

  loadingElement.innerHTML =
    '<div class="spinner-border" role="status"><span class="sr-only">Loading...</span></div>';
  loadingElement.style.display = "none";
  document.body.appendChild(loadingElement);

  let mediaRecorder;
  let audioChunks = [];

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    statusElement.textContent =
      "Media Recorder API is not supported in this browser.";
    return;
  }

  startButton.addEventListener("click", async () => {
    startButton.disabled = true;
    stopButton.disabled = false;
    statusElement.textContent = "";

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true, // Or audio: { channelCount: 1 } for mono
      });

      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
        audioChunks = [];

        try {
          const formData = new FormData();
          formData.append("audio", audioBlob, "recording.wav");

          loadingElement.style.display = "block";
          resultsElement.style.display = "none";
          statusElement.textContent = "Processing...";

          const response = await fetch(
            "https://yourdomain.com/asr", // Replace with your Sanic backend URL
            {
              method: "POST",
              body: formData,
            },
          );

          loadingElement.style.display = "none";
          resultsElement.style.display = "block";

          if (response.ok) {
            const data = await response.json();

            transcriptionElement.textContent = data.transcription;
            translationElement.textContent = data.translation;

            // --- Display EMR Data ---
            emrDataElement.textContent = ""; // Clear previous content
            for (const key in data.emr_data) {
              emrDataElement.textContent += `${key}: ${data.emr_data[key]}\n`;
            }

            // --- Display Suggestions ---
            suggestionsElement.textContent = ""; // Clear previous content
            for (const key in data.suggestions) {
              suggestionsElement.textContent += `${key}: ${data.suggestions[key]}\n`;
            }
          } else {
            const errorData = await response.json();
            const errorMessage =
              errorData.error || "An error occurred during processing.";
            statusElement.textContent = `Error: ${errorMessage}`;
          }
        } catch (error) {
          loadingElement.style.display = "none";
          resultsElement.style.display = "block";
          statusElement.textContent = `Error: ${error.message}`;
          console.error("Error during fetch:", error);
        }
      };

      mediaRecorder.start();
    } catch (error) {
      statusElement.textContent = "Error accessing microphone.";
      console.error("Error:", error);
    }
  });

  stopButton.addEventListener("click", () => {
    if (mediaRecorder) {
      startButton.disabled = false;
      stopButton.disabled = true;
      statusElement.textContent = "Processing...";
      mediaRecorder.stop();
    }
  });

  // --- Audio Upload Feature ---
  const audioUploadInput = document.getElementById("audioUploadInput");
  const uploadButton = document.getElementById("uploadButton");

  uploadButton.addEventListener("click", () => {
    audioUploadInput.click(); // Trigger the file input when the button is clicked
  });

  audioUploadInput.addEventListener("change", async () => {
    const file = audioUploadInput.files[0];
    if (file) {
      try {
        const formData = new FormData();
        formData.append("audio", file);

        loadingElement.style.display = "block";
        resultsElement.style.display = "none";
        statusElement.textContent = "Processing...";

        const response = await fetch(
          "https://yourdomain.com/asr/asr", // Replace with your backend URL
          {
            method: "POST",
            body: formData,
          },
        );

        loadingElement.style.display = "none";
        resultsElement.style.display = "block";

        if (response.ok) {
          const data = await response.json();

          transcriptionElement.textContent = data.transcription;
          translationElement.textContent = data.translation;

          // --- Display EMR Data ---
          emrDataElement.textContent = ""; // Clear previous content
          for (const key in data.emr_data) {
            emrDataElement.textContent += `${key}: ${data.emr_data[key]}\n`;
          }

          // --- Display Suggestions ---
          suggestionsElement.textContent = ""; // Clear previous content
          for (const key in data.suggestions) {
            suggestionsElement.textContent += `${key}: ${data.suggestions[key]}\n`;
          }
        } else {
          const errorData = await response.json();
          const errorMessage =
            errorData.error || "An error occurred during processing.";
          statusElement.textContent = `Error: ${errorMessage}`;
        }
      } catch (error) {
        loadingElement.style.display = "none";
        resultsElement.style.display = "block";
        statusElement.textContent = `Error: ${error.message}`;
        console.error("Error during fetch:", error);
      }
    }
  });
  // --- End Audio Upload Feature ---

  // --- Download Report Feature ---
  downloadReportButton.addEventListener("click", () => {
    const patientName = document.getElementById("patientNameInput").value;
    const patientAge = document.getElementById("patientAgeInput").value;
    const patientAddress = document.getElementById("patientAddressInput").value;
    const patientSex = document.getElementById("patientSexInput").value;
    const patientPhone = document.getElementById("patientPhoneInput").value;
    const emrData = document.getElementById("emr-data").textContent;
    const suggestions = document.getElementById("suggestions").textContent;

    const reportContent = `
Patient Details:
Name: ${patientName}
Age: ${patientAge}
Address: ${patientAddress}
Sex: ${patientSex}
Phone: ${patientPhone}

EMR Data:
${emrData}

Suggestions:
${suggestions}
`;

    downloadTextFile(reportContent, `${patientName}_report.txt`);
  });

  function downloadTextFile(content, filename) {
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = filename;

    document.body.appendChild(link);
    link.click();

    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
  // --- End Download Report Feature ---
});
