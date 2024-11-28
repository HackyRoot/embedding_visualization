document.addEventListener('DOMContentLoaded', () => {
    const textInput = document.getElementById('textInput');
    const modelSelect = document.getElementById('modelSelect');
    const generateBtn = document.getElementById('generateBtn');
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error');
    const plotDiv = document.getElementById('plot');

    let currentPlot = null;

    function showLoading(show) {
        loadingDiv.classList.toggle('hidden', !show);
        generateBtn.disabled = show;
    }

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
        setTimeout(() => {
            errorDiv.classList.add('hidden');
        }, 5000);
    }

    function visualizeEmbeddings(reducedEmbeddings, labels) {
        const colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ];

        const data = [{
            type: 'scatter3d',
            mode: 'markers+text',
            x: reducedEmbeddings.map(e => e[0]),
            y: reducedEmbeddings.map(e => e[1]),
            z: reducedEmbeddings.map(e => e[2]),
            text: labels,
            textposition: 'top center',
            marker: {
                size: 8,
                color: labels.map((_, i) => colors[i % colors.length]),
                opacity: 0.8
            },
            hovertemplate:
                'Word: %{text}<br>' +
                'X: %{x:.4f}<br>' +
                'Y: %{y:.4f}<br>' +
                'Z: %{z:.4f}<br>' +
                '<extra></extra>'
        }];

        const layout = {
            title: '3D Word Embedding Space',
            scene: {
                xaxis: { 
                    title: "X Axis",
                    titlefont: { size: 12 }
                },
                yaxis: { 
                    title: "Y Axis",
                    titlefont: { size: 12 }
                },
                zaxis: { 
                    title: "Z Axis",
                    titlefont: { size: 12 }
                },
                camera: {
                    eye: { x: 1.5, y: 1.5, z: 1.5 }
                }
            },
            margin: {
                l: 0,
                r: 0,
                b: 0,
                t: 30
            },
            showlegend: false
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToAdd: [{
                name: 'Reset Camera',
                icon: Plotly.Icons.home,
                click: function(gd) {
                    Plotly.relayout(gd, {
                        'scene.camera': {
                            eye: { x: 1.5, y: 1.5, z: 1.5 }
                        }
                    });
                }
            }]
        };

        if (currentPlot) {
            Plotly.react(plotDiv, data, layout, config);
        } else {
            Plotly.newPlot(plotDiv, data, layout, config);
            currentPlot = true;
        }
    }

    generateBtn.addEventListener('click', async () => {
        const text = textInput.value.trim();
        const model = modelSelect.value;

        if (!text) {
            showError('Please enter some text');
            return;
        }

        if (text.split(',').length < 3) {
            showError('Please enter at least 3 words separated by commas');
            return;
        }

        showLoading(true);
        try {
            const response = await fetch('/get_embedding', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text, model })
            });

            if (!response.ok) {
                throw new Error('Failed to generate embedding');
            }

            const data = await response.json();
            visualizeEmbeddings(data.reduced_embeddings, data.labels);
        } catch (error) {
            showError(error.message);
        } finally {
            showLoading(false);
        }
    });
});
