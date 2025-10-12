document.addEventListener('DOMContentLoaded', function () {
    // Modal elements
    const modal = document.getElementById('exampleModal');
    const closeBtn = document.querySelector('.close-btn');
    const exampleButtons = document.querySelectorAll('.example-btn');
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');

    // Example content
    const examples = {
        1: {
            title: "Map Domain Examples",
            description: "135 high-quality queries based on Chinese geographical landmarks, using GoogleMap MCP server and Amap MCP server.",
            result: `GT: 大连观光塔`,
            problem: `在大连市中山区，寻找一个符合以下特征的地标： \n1. 在行政区划上属于中山区（区划代码210202）。 \n2. 从青泥洼桥地铁站步行至此约需31分59秒，步行距离约2.40公里。 \n3. 从大连站驾车到此全程约4.22公里，预计用时约12分59秒；而从大连站乘坐地铁5号线至劳动公园站并步行到达的公共交通方案总用时约42分22秒。该地标的名称是？`
        },
        2: {
            title: "Medical/Bio Domain Examples",
            description: "83 high-quality queries based on Drug, Gene, rare disease, and NCT ID, using BioMCP server",
            result: `GT: NCT07180706`,
            problem: `Which clinical trial meets these criteria? \n1. Uses an FDA De Novo-approved ultrasound device for tumor ablation without needles or heat. \n2. Aims to alleviate symptoms in adults with non-operable abdominal tumors (3-10 cm).\n3. Takes place at a university hospital. \n4. Measures outcomes using SF-36 and VAS scores over six months. \n5. Involves mechanical tissue disruption via focused ultrasound.`
        },
        3: {
            title: "Video Domain Examples",
            description: "100 high-quality queries based on Youtube Videos,using Youtube MCP servers and Serpapi interface.",
            result: "GT: https://www.youtube.com/watch?v=9lU_IGeaizE",
            problem: "On YouTube, there is a video that meets all of the following conditions:\n1) Uploaded on September 2, 2025;\n2) Duration is approximately 7 minutes;\n3) The channel has around 30.5 thousand subscribers as of 2025-09;\n4) A top comment includes the phrase \"Piga hit after hit\";\n5) The description contains the hashtag \"#NgommaBenga\".\nWhich video is this? Provide its URL.",
        },
        4: {
            title: "Web Domain Examples",
            description: "100 high-quality queries based on textual sources spanning a broad range of internet domains, using web-search and web-parse functions.",
            result: `GT: Shiwa Ng'andu`,
            problem: `Link these hints: A woman once took over a large looped construction when her spouse fell ill, and during a war she ran an auxiliary facility tied to a principal military hospital in the capital. Her nephew, later accorded national funeral honors unusual for someone of his background, built an English-style home near a lake whose local name links royalty with a reptile. What is the name of that residence?`
        },
        5: {
            title: "Finance Domain Examples",
            description: "100 high-quality queries based on mainstream US stock companies, using FMP MCP server.",
            result: `GT: RIVN`,
            problem: `Which company reported a second-quarter 2025 revenue between $1 billion and $2 billion, had a negative net income for that quarter, and, as of September 19, 2025, experienced a six-month stock price increase of over 30% and a one-month increase of over 15%?`
        },
        6: {
            title: "Multi-Domain Examples",
            description: "Simple Description for multi-domain examples.",
            result: `To be done.`,
            problem: `To be done.`
        }
    };

    // Current example being viewed
    let currentExample = null;

    // Format time for messages
    function formatTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // Add a message to the chat
    function addMessage(content, isUser = false, isCode = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

        // Create icon element
        const iconDiv = document.createElement('div');
        iconDiv.className = `message-icon ${isUser ? 'user-icon' : 'bot-icon'}`;

        // Create SVG icon
        const svgNS = "http://www.w3.org/2000/svg";
        const svg = document.createElementNS(svgNS, "svg");
        svg.setAttribute("viewBox", "0 0 24 24");

        if (isUser) {
            // User icon - person silhouette
            const path = document.createElementNS(svgNS, "path");
            path.setAttribute("d", "M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z");
            svg.appendChild(path);
        } else {
            // Bot icon - robot face
            const path1 = document.createElementNS(svgNS, "path");
            path1.setAttribute("d", "M20 9V7c0-1.1-.9-2-2-2h-3c0-1.66-1.34-3-3-3S9 3.34 9 5H6c-1.1 0-2 .9-2 2v2c-1.66 0-3 1.34-3 3s1.34 3 3 3v4c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2v-4c1.66 0 3-1.34 3-3s-1.34-3-3-3z");
            const path2 = document.createElementNS(svgNS, "path");
            path2.setAttribute("d", "M7.5 11.5c.55 0 1-.45 1-1s-.45-1-1-1-1 .45-1 1 .45 1 1 1zm9 0c.55 0 1-.45 1-1s-.45-1-1-1-1 .45-1 1 .45 1 1 1z");
            svg.appendChild(path1);
            svg.appendChild(path2);
        }

        iconDiv.appendChild(svg);

        // Create content wrapper
        // todo polish font size and color for those content wrapper
        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'message-content-wrapper';

        const messageHeader = document.createElement('div');
        messageHeader.className = 'message-Header';
        messageHeader.textContent = isUser ? 'Query' : 'Assistant';

        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        timeSpan.textContent = formatTime();
        messageHeader.appendChild(timeSpan);

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        if (isCode) {
            const codeBlock = document.createElement('pre');
            codeBlock.className = 'code-block';
            codeBlock.textContent = content;
            messageContent.appendChild(codeBlock);
        } else {
            messageContent.textContent = content;
        }

        contentWrapper.appendChild(messageHeader);
        contentWrapper.appendChild(messageContent);
        messageDiv.appendChild(iconDiv);
        messageDiv.appendChild(contentWrapper);
        chatMessages.appendChild(messageDiv);

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Initialize chat with example info
    function initChat(exampleId) {
        const example = examples[exampleId];
        if (!example) return;

        currentExample = exampleId;

        // Clear previous messages
        chatMessages.innerHTML = '';

        // Add initial bot messages
        // addMessage(`Welcome to ${example.title}!`);
        addMessage(example.problem, true);
        addMessage(example.result)
        // addMessage("Would you like to see the code implementation?", false);
    }

    // Example button event listeners
    exampleButtons.forEach(button => {
        button.addEventListener('click', function () {
            const exampleId = this.getAttribute('data-example');

            // --- 修改开始 ---
            const h3Element = document.getElementById('example title');
            const example = examples[exampleId];

            if (h3Element && example) {
                // 关键：将对应示例的 description 赋给 h3 元素
                h3Element.textContent = example.title;
            }
            // --- 修改结束 ---
            initChat(exampleId);
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';// Prevent background scrolling
        });
    });

    // Close modal when close button is clicked
    closeBtn.addEventListener('click', function () {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';// Re-enable scrolling
    });

    // Close modal when clicking outside the modal content
    modal.addEventListener('click', function (event) {
        if (event.target === modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';// Re-enable scrolling
        }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && modal.style.display === 'block') {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';// Re-enable scrolling
        }
    });

    // Send button event listener
    sendBtn.addEventListener('click', function () {
        const userInput = chatInput.value.trim();
        if (userInput) {
            // Add user message
            addMessage(userInput, true);
            chatInput.value = '';

            // Simulate bot response after a short delay
            setTimeout(() => {
                addMessage("Read the paper for more information and examples!🫡", false);
            }, 500);
        }
    });

    // Send message on Enter key
    chatInput.addEventListener('keypress', function (event) {
        if (event.key === 'Enter') {
            sendBtn.click();
        }
    });
});