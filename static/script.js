 async function startExecution() {
        const outputDiv = document.getElementById('output');
        const startBtn = document.getElementById('startBtn');
        const indicator = document.getElementById('indicator');
        const statusText = document.getElementById('statusText');
        const terminalWindow = document.getElementById('terminalWindow');

        // Reset UI
        outputDiv.textContent = ""; 
        startBtn.disabled = true;
        statusText.textContent = "Running minimal.py...";
        indicator.className = "status-indicator status-running";

        try {
            // Fetch the stream
            const response = await fetch('/run-script');
            
            // Create a reader to read the stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                // Read chunks of data
                const { value, done } = await reader.read();
                if (done) break;

                // Decode chunk to text
                const text = decoder.decode(value);
                
                // Append text to terminal
                outputDiv.textContent += text;
                
                // Auto-scroll to bottom
                terminalWindow.scrollTop = terminalWindow.scrollHeight;
            }

            statusText.textContent = "Execution Complete";
            indicator.className = "status-indicator status-done";

        } catch (error) {
            outputDiv.textContent += `\n❌ Connection Error: ${error}`;
        } finally {
            startBtn.disabled = false;
        }
    }

    // Optional: Auto-start on load if desired
    // window.onload = startExecution;