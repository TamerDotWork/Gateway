 // This ensures the page stays scrolled to the latest log
    window.scrollTo(0, document.body.scrollHeight);
    const terminal = document.querySelector('.terminal-output');
    
    // Create an observer to scroll automatically when new content arrives
    const observer = new MutationObserver(() => {
        terminal.scrollTop = terminal.scrollHeight;
    });
    observer.observe(terminal, { childList: true, subtree: true, characterData: true });