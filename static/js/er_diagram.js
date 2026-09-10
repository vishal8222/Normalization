function renderERDiagram(containerId, erData) {
    const container = document.getElementById(containerId);
    if (!container || !erData || !erData.nodes) return;

    // Clear previous
    container.innerHTML = '';

    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    
    // Dynamic sizing
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '400px');
    svg.style.backgroundColor = '#f8f9fa';
    svg.style.borderRadius = '8px';

    const nodeWidth = 200;
    const headerHeight = 30;
    const rowHeight = 25;
    const padding = 20;

    let currentX = 50;
    let currentY = 50;

    // Node positioning logic (simple horizontal layout)
    const nodePositions = {};

    erData.nodes.forEach((node, index) => {
        const nodeHeight = headerHeight + (node.columns.length * rowHeight) + 10;
        
        nodePositions[node.id] = {
            x: currentX,
            y: currentY,
            width: nodeWidth,
            height: nodeHeight
        };

        // Draw Table Group
        const g = document.createElementNS(svgNS, "g");
        g.setAttribute('transform', `translate(${currentX}, ${currentY})`);
        
        // Drop shadow def
        const defs = document.createElementNS(svgNS, 'defs');
        defs.innerHTML = `
            <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
                <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.2"/>
            </filter>
        `;
        svg.appendChild(defs);

        // Rect for whole table
        const rect = document.createElementNS(svgNS, "rect");
        rect.setAttribute('width', nodeWidth);
        rect.setAttribute('height', nodeHeight);
        rect.setAttribute('rx', 5);
        rect.setAttribute('fill', 'white');
        rect.setAttribute('stroke', '#1B4F72');
        rect.setAttribute('stroke-width', '2');
        rect.setAttribute('filter', 'url(#shadow)');
        g.appendChild(rect);

        // Header rect
        const headerRect = document.createElementNS(svgNS, "rect");
        headerRect.setAttribute('width', nodeWidth);
        headerRect.setAttribute('height', headerHeight);
        headerRect.setAttribute('rx', 5);
        headerRect.setAttribute('fill', '#1B4F72');
        g.appendChild(headerRect);

        // Header text
        const title = document.createElementNS(svgNS, "text");
        title.setAttribute('x', nodeWidth / 2);
        title.setAttribute('y', 20);
        title.setAttribute('fill', 'white');
        title.setAttribute('font-weight', 'bold');
        title.setAttribute('font-size', '14');
        title.setAttribute('text-anchor', 'middle');
        title.setAttribute('font-family', 'Inter, sans-serif');
        title.textContent = node.id;
        g.appendChild(title);

        // Columns
        node.columns.forEach((col, i) => {
            const colY = headerHeight + 5 + (i * rowHeight);
            
            let icon = '';
            let fill = '#333';
            if (col.is_primary_key) { icon = '🔑 '; fill = '#28B463'; } // Green PK
            else if (col.is_foreign_key) { icon = '🔗 '; fill = '#F39C12'; } // Orange FK

            const text = document.createElementNS(svgNS, "text");
            text.setAttribute('x', 10);
            text.setAttribute('y', colY + 15);
            text.setAttribute('fill', fill);
            text.setAttribute('font-size', '12');
            text.setAttribute('font-family', 'Inter, sans-serif');
            text.textContent = `${icon}${col.name}`;
            g.appendChild(text);

            // Column line separator
            if (i < node.columns.length - 1) {
                const line = document.createElementNS(svgNS, "line");
                line.setAttribute('x1', 0);
                line.setAttribute('y1', colY + 20);
                line.setAttribute('x2', nodeWidth);
                line.setAttribute('y2', colY + 20);
                line.setAttribute('stroke', '#eee');
                g.appendChild(line);
            }
        });

        svg.appendChild(g);

        // Advance layout position
        currentX += nodeWidth + 100;
        if (currentX > 800) {
            currentX = 50;
            currentY += 250;
        }
    });

    // Draw Edges
    if (erData.edges) {
        erData.edges.forEach(edge => {
            const fromPos = nodePositions[edge.from];
            const toPos = nodePositions[edge.to];
            
            if (fromPos && toPos) {
                // Simple straight line from center right to center left (or vice versa)
                const isLeftToRight = fromPos.x < toPos.x;
                
                const x1 = isLeftToRight ? fromPos.x + fromPos.width : fromPos.x;
                const y1 = fromPos.y + (fromPos.height / 2);
                
                const x2 = isLeftToRight ? toPos.x : toPos.x + toPos.width;
                const y2 = toPos.y + (toPos.height / 2);

                // Draw path
                const path = document.createElementNS(svgNS, "path");
                // Simple curve
                const d = `M ${x1} ${y1} C ${x1 + (isLeftToRight?50:-50)} ${y1}, ${x2 - (isLeftToRight?50:-50)} ${y2}, ${x2} ${y2}`;
                path.setAttribute('d', d);
                path.setAttribute('stroke', '#F39C12');
                path.setAttribute('stroke-width', '2');
                path.setAttribute('fill', 'none');
                svg.insertBefore(path, svg.firstChild); // put behind nodes

                // Label
                const text = document.createElementNS(svgNS, "text");
                text.setAttribute('x', (x1 + x2) / 2);
                text.setAttribute('y', ((y1 + y2) / 2) - 10);
                text.setAttribute('fill', '#1B4F72');
                text.setAttribute('font-size', '12');
                text.setAttribute('font-weight', 'bold');
                text.setAttribute('text-anchor', 'middle');
                text.textContent = edge.type || 'rel';
                
                // Add tiny white background for label readability
                const textBg = document.createElementNS(svgNS, "rect");
                textBg.setAttribute('x', ((x1 + x2) / 2) - 15);
                textBg.setAttribute('y', ((y1 + y2) / 2) - 22);
                textBg.setAttribute('width', 30);
                textBg.setAttribute('height', 15);
                textBg.setAttribute('fill', 'rgba(255,255,255,0.8)');
                
                svg.appendChild(textBg);
                svg.appendChild(text);
            }
        });
    }

    container.appendChild(svg);
}

// Make globally available
window.renderERDiagram = renderERDiagram;
