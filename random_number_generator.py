<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎰 Smooth Rolling Number Generator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
        }

        .container {
            text-align: center;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        h1 {
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        .controls {
            margin-bottom: 30px;
            display: flex;
            gap: 20px;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
        }

        .control-group {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 5px;
        }

        .control-group label {
            font-size: 0.9em;
            opacity: 0.9;
        }

        .control-group input {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            border-radius: 5px;
            padding: 5px 10px;
            color: white;
            width: 80px;
        }

        .number-container {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }

        .number-box {
            width: 80px;
            height: 80px;
            background: linear-gradient(45deg, #4A90E2, #9013FE);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5em;
            font-weight: bold;
            color: white;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .number-box.rolling {
            background: linear-gradient(45deg, #FF6B6B, #FFE66D);
            animation: rollPulse 0.1s infinite alternate;
        }

        .number-box.stopping {
            background: linear-gradient(45deg, #4ECDC4, #44A08D);
            animation: celebrate 0.5s ease-out;
        }

        @keyframes rollPulse {
            from {
                transform: scale(1);
                box-shadow: 0 8px 25px rgba(255, 107, 107, 0.4);
            }
            to {
                transform: scale(1.05);
                box-shadow: 0 12px 30px rgba(255, 107, 107, 0.6);
            }
        }

        @keyframes celebrate {
            0% {
                transform: scale(1);
            }
            50% {
                transform: scale(1.2);
            }
            100% {
                transform: scale(1.1);
            }
        }

        .roll-button {
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            border: none;
            color: white;
            padding: 15px 40px;
            font-size: 1.2em;
            font-weight: bold;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
            margin: 10px;
        }

        .roll-button:hover:not(:disabled) {
            transform: translateY(-3px);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
        }

        .roll-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .stats {
            margin-top: 20px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 15px;
            opacity: 0.9;
        }

        .stat-box {
            background: rgba(255, 255, 255, 0.1);
            padding: 10px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .stat-box h3 {
            font-size: 0.9em;
            margin-bottom: 5px;
            opacity: 0.8;
        }

        .stat-box .value {
            font-size: 1.5em;
            font-weight: bold;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            margin: 20px 0;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(45deg, #4ECDC4, #44A08D);
            width: 0%;
            transition: width 0.1s ease;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎰 Smooth Rolling Numbers</h1>
        
        <div class="controls">
            <div class="control-group">
                <label>Rolling Speed (ms)</label>
                <input type="number" id="rollSpeed" value="50" min="20" max="200">
            </div>
            <div class="control-group">
                <label>Duration (seconds)</label>
                <input type="number" id="duration" value="3" min="1" max="10" step="0.5">
            </div>
            <div class="control-group">
                <label>Digits</label>
                <input type="number" id="digitCount" value="8" min="1" max="12">
            </div>
        </div>

        <div class="number-container" id="numberContainer">
            <!-- Numbers will be generated here -->
        </div>

        <div class="progress-bar">
            <div class="progress-fill" id="progressFill"></div>
        </div>

        <button class="roll-button" id="rollButton" onclick="startRolling()">
            🎲 Start Rolling
        </button>

        <div class="stats" id="stats">
            <!-- Stats will appear here -->
        </div>
    </div>

    <script>
        let isRolling = false;
        let rollIntervals = [];
        let finalNumbers = [];
        let currentNumbers = [];

        function createNumberBoxes() {
            const container = document.getElementById('numberContainer');
            const digitCount = parseInt(document.getElementById('digitCount').value);
            
            container.innerHTML = '';
            currentNumbers = Array(digitCount).fill('?');
            
            for (let i = 0; i < digitCount; i++) {
                const box = document.createElement('div');
                box.className = 'number-box';
                box.id = `number-${i}`;
                box.textContent = '?';
                container.appendChild(box);
            }
        }

        function startRolling() {
            if (isRolling) return;

            const rollSpeed = parseInt(document.getElementById('rollSpeed').value);
            const duration = parseFloat(document.getElementById('duration').value) * 1000;
            const digitCount = parseInt(document.getElementById('digitCount').value);
            
            isRolling = true;
            document.getElementById('rollButton').disabled = true;
            document.getElementById('rollButton').textContent = '🎲 Rolling...';
            
            // Generate final numbers
            finalNumbers = Array.from({length: digitCount}, () => Math.floor(Math.random() * 10));
            
            // Clear previous intervals
            rollIntervals.forEach(interval => clearInterval(interval));
            rollIntervals = [];

            // Start progress bar
            const progressFill = document.getElementById('progressFill');
            const startTime = Date.now();
            const progressInterval = setInterval(() => {
                const elapsed = Date.now() - startTime;
                const progress = Math.min((elapsed / duration) * 100, 100);
                progressFill.style.width = progress + '%';
                
                if (progress >= 100) {
                    clearInterval(progressInterval);
                }
            }, 50);

            // Start rolling for each digit
            for (let i = 0; i < digitCount; i++) {
                const box = document.getElementById(`number-${i}`);
                box.className = 'number-box rolling';
                
                // Each digit stops at a different time for cascade effect
                const stopTime = (duration * 0.3) + (i * (duration * 0.7) / digitCount);
                
                const rollInterval = setInterval(() => {
                    if (!isRolling) {
                        clearInterval(rollInterval);
                        return;
                    }
                    
                    const randomNum = Math.floor(Math.random() * 10);
                    box.textContent = randomNum;
                    currentNumbers[i] = randomNum;
                }, rollSpeed);
                
                rollIntervals.push(rollInterval);
                
                // Stop this digit after its designated time
                setTimeout(() => {
                    clearInterval(rollInterval);
                    box.textContent = finalNumbers[i];
                    box.className = 'number-box stopping';
                    currentNumbers[i] = finalNumbers[i];
                    
                    // Check if all digits have stopped
                    const allStopped = currentNumbers.every((num, index) => num === finalNumbers[index]);
                    if (allStopped) {
                        setTimeout(() => {
                            finishRolling();
                        }, 500);
                    }
                }, stopTime);
            }
        }

        function finishRolling() {
            isRolling = false;
            document.getElementById('rollButton').disabled = false;
            document.getElementById('rollButton').textContent = '🎲 Roll Again';
            
            // Update all boxes to final state
            finalNumbers.forEach((num, i) => {
                const box = document.getElementById(`number-${i}`);
                box.className = 'number-box';
                box.textContent = num;
            });
            
            updateStats();
            
            // Reset progress bar
            setTimeout(() => {
                document.getElementById('progressFill').style.width = '0%';
            }, 1000);
        }

        function updateStats() {
            const sum = finalNumbers.reduce((a, b) => a + b, 0);
            const avg = (sum / finalNumbers.length).toFixed(1);
            const max = Math.max(...finalNumbers);
            const min = Math.min(...finalNumbers);
            
            const statsHtml = `
                <div class="stat-box">
                    <h3>Sum</h3>
                    <div class="value">${sum}</div>
                </div>
                <div class="stat-box">
                    <h3>Average</h3>
                    <div class="value">${avg}</div>
                </div>
                <div class="stat-box">
                    <h3>Max</h3>
                    <div class="value">${max}</div>
                </div>
                <div class="stat-box">
                    <h3>Min</h3>
                    <div class="value">${min}</div>
                </div>
            `;
            
            document.getElementById('stats').innerHTML = statsHtml;
        }

        // Initialize on page load
        window.onload = function() {
            createNumberBoxes();
            
            // Update boxes when digit count changes
            document.getElementById('digitCount').addEventListener('change', createNumberBoxes);
        };
    </script>
</body>
</html>
