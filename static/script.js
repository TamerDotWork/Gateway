            // Dynamic WebSocket URL generation
            const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
            
            // Ensure path ends with / so it matches the Python route logic
            let path = window.location.pathname;
            if (!path.endsWith('/')) path += '/';
            
            // Build the full WebSocket URL
            const wsUrl = `${protocol}://${window.location.host}${path}`;
            console.log("Connecting to Dashboard WS:", wsUrl);

            const ws = new WebSocket(wsUrl);
            const dot = document.getElementById("dot");
            const statusText = document.getElementById("status-text");
            const statusContainer = document.getElementByClass("tag");

            ws.onopen = () => {
                
                dot.classList.remove("failure");
                dot.classList.add("success");
                statusContainer.classList.remove("failure");
                statusContainer.classList.add("success");
                // dot.style.backgroundColor = "#00ff00";
                statusText.innerText = "Live Connected";
                // Keep-alive ping
                setInterval(() => { if(ws.readyState===1) ws.send("ping"); }, 2000);
            };

            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    if(data.requests_from_user !== undefined) {
                        document.getElementById("req").innerText = data.requests_from_user;
                        document.getElementById("res").innerText = data.responses_from_llm;
                        document.getElementById("err").innerText = data.errors;
                        document.getElementById("last_p").innerText = data.last_prompt;
                    }
                } catch(e) { 
                    // Ignore non-JSON messages (like ping responses)
                }
            };

            ws.onclose = () => {
                dot.classList.remove("success");
                dot.classList.add("failure");
                statusContainer.classList.remove("success");
                statusContainer.classList.add("failure");
                // dot.style.backgroundColor = "red";
                statusText.innerText = "Disconnected";
            };