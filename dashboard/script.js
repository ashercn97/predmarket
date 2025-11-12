(function() {
    const API_URL = 'http://localhost:8000';
    let sweepsData = [];
    let expiringData = [];
    let activeTab = 'sweeps';
    let isHovering = false;
    let currentPage = 1;
    const ITEMS_PER_PAGE = 15;
    let previousSweepIds = new Set();

    // Sports and crypto keywords
    const SPORTS_KEYWORDS = ['mlb-', 'nfl-', 'nba-', 'nhl-', 'ufc-', 'f1-', 'premier-league',
        'soccer', 'football', 'baseball', 'basketball', 'hockey', 'tennis',
        'golf', 'boxing', 'mma', 'olympics', 'world-cup'];

    const CRYPTO_KEYWORDS = ['bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'sol',
        'xrp', 'ripple', 'doge', 'dogecoin', 'ada', 'cardano',
        'matic', 'polygon', 'crypto', 'cryptocurrency'];

    function isSportsMarket(slug, title) {
        const slugLower = (slug || '').toLowerCase();
        const titleLower = (title || '').toLowerCase();
        return SPORTS_KEYWORDS.some(kw => slugLower.includes(kw) || titleLower.includes(kw));
    }

    function isCryptoMarket(slug, title) {
        const slugLower = (slug || '').toLowerCase();
        const titleLower = (title || '').toLowerCase();
        return CRYPTO_KEYWORDS.some(kw => slugLower.includes(kw) || titleLower.includes(kw));
    }

    async function fetchData() {
        if (isHovering) return;
        try {
            const [sweepsRes, expiringRes] = await Promise.all([
                fetch(`${API_URL}/api/polymarket/sweeps`).then(r => r.json()),
                fetch(`${API_URL}/api/polymarket/expiring`).then(r => r.json())
            ]);

            const newSweeps = sweepsRes.data || [];
            expiringData = expiringRes.data || [];

            // Filter out sweeps with blank/missing critical data
            const validSweeps = newSweeps.filter(sweep => {
                return sweep.title && sweep.title.trim() !== '' &&
                       sweep.outcome && sweep.outcome.trim() !== '';
            });

            // Sort by timestamp FIRST (newest first) to prevent flashing
            validSweeps.sort((a, b) => b.timestamp - a.timestamp);

            // Track new sweeps for flash animation
            const newSweepIds = new Set();
            validSweeps.forEach(sweep => {
                const id = sweep.transactionHash || `${sweep.timestamp}-${sweep.usd_amount}`;
                newSweepIds.add(id);
                if (!previousSweepIds.has(id)) {
                    sweep.isNew = true;
                }
            });
            previousSweepIds = newSweepIds;

            sweepsData = validSweeps;
            renderTab(activeTab);
        } catch (error) {
            console.error('Error fetching data:', error);
            document.getElementById('content-wrapper').innerHTML = `<div style="text-align: center; padding: 60px 20px; color: #FF6B88;"><div style="font-size: 1.2rem; margin-bottom: 10px;">⚠️ Backend not running</div><div style="font-size: 0.9rem;">Start the backend service to see live data</div></div>`;
        }
    }

    function formatUSD(amount) { return '$' + Math.floor(amount).toLocaleString(); }

    function timeAgo(timestamp) {
        const seconds = Math.floor(Date.now() / 1000 - timestamp);
        if (seconds < 60) return `${seconds}s ago`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        return `${Math.floor(seconds / 86400)}d ago`;
    }

    function getAmountClass(amount) {
        if (amount >= 500000) return 'amount-legendary';
        if (amount >= 250000) return 'amount-godlike';
        if (amount >= 100000) return 'amount-giant';
        if (amount >= 50000) return 'amount-huge';
        if (amount >= 10000) return 'amount-large';
        if (amount >= 5000) return 'amount-medium';
        return 'amount-small';
    }

    function getSweepsHeatmapStyle(amount) {
        // Returns emoji, text class, and background color for individual sweeps (lower thresholds)
        if (amount >= 5000) return { emoji: '🔥', class: 'amount-giant', bg: 'rgba(16, 185, 129, 0.18)' }; // $5000+ Brightest green
        if (amount >= 1000) return { emoji: '💰', class: 'amount-large', bg: 'rgba(74, 222, 128, 0.14)' }; // $1000+ Medium green
        if (amount >= 500) return { emoji: '', class: 'amount-medium', bg: 'rgba(250, 204, 21, 0.12)' }; // $500+ Yellow
        if (amount >= 300) return { emoji: '', class: 'amount-small', bg: 'rgba(251, 146, 60, 0.08)' }; // $300+ Light orange
        return { emoji: '', class: 'amount-small', bg: 'transparent' }; // Under $300 no background
    }

    function getHeatmapStyle(amount) {
        // Returns emoji, text class, and background color for aggregated volumes (higher thresholds)
        if (amount >= 100000) return { emoji: '🔥', class: 'amount-giant', bg: 'rgba(16, 185, 129, 0.18)' }; // Brightest green
        if (amount >= 50000) return { emoji: '⚡', class: 'amount-huge', bg: 'rgba(74, 222, 128, 0.14)' }; // Medium green
        if (amount >= 10000) return { emoji: '💰', class: 'amount-large', bg: 'rgba(250, 204, 21, 0.12)' }; // Yellow
        if (amount >= 5000) return { emoji: '', class: 'amount-medium', bg: 'rgba(251, 146, 60, 0.08)' }; // Light orange
        return { emoji: '', class: 'amount-small', bg: 'transparent' }; // No background for small
    }

    function getFilteredSweeps() {
        const minAmount = parseFloat(document.getElementById('filter-min-amount').value) || 0;
        const ignoreSports = document.getElementById('filter-ignore-sports').checked;
        const ignoreCrypto = document.getElementById('filter-ignore-crypto').checked;

        return sweepsData.filter(sweep => {
            if (sweep.usd_amount < minAmount) return false;
            if (ignoreSports && isSportsMarket(sweep.market_slug, sweep.title)) return false;
            if (ignoreCrypto && isCryptoMarket(sweep.market_slug, sweep.title)) return false;
            return true;
        });
    }

    function renderPagination(totalItems) {
        const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
        const pagination = document.getElementById('pagination');

        if (totalPages <= 1) {
            pagination.style.display = 'none';
            return;
        }

        pagination.style.display = 'flex';
        let html = '';

        // Previous button
        html += `<button class="page-btn" onclick="window.dashboardPagination.goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>◀</button>`;

        // Page numbers (show max 10)
        const startPage = Math.max(1, currentPage - 4);
        const endPage = Math.min(totalPages, startPage + 9);

        if (startPage > 1) {
            html += `<button class="page-btn" onclick="window.dashboardPagination.goToPage(1)">1</button>`;
            if (startPage > 2) html += `<span style="color: #666;">...</span>`;
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="window.dashboardPagination.goToPage(${i})">${i}</button>`;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) html += `<span style="color: #666;">...</span>`;
            html += `<button class="page-btn" onclick="window.dashboardPagination.goToPage(${totalPages})">${totalPages}</button>`;
        }

        // Next button
        html += `<button class="page-btn" onclick="window.dashboardPagination.goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>▶</button>`;

        pagination.innerHTML = html;
    }

    window.dashboardPagination = {
        goToPage: function(page) {
            if (page < 1) return;
            currentPage = page;
            renderTab(activeTab);
        }
    };

    function renderTab(tab) {
        // Only reset to page 1 if switching tabs
        if (activeTab !== tab) {
            currentPage = 1;
        }
        activeTab = tab;
        switch(tab) {
            case 'sweeps': renderSweepsTab(); break;
            case 'whales': renderWhalesTab(); break;
            case 'no-markets': renderNOMarketsTab(); break;
            case 'edge-markets': renderEdgeMarketsTab(); break;
            case 'closing-soon': renderClosingSoonTab(); break;
            case 'clusters': renderClustersTab(); break;
        }
    }

    function renderSweepsTab() {
        const filtered = getFilteredSweeps();
        if (filtered.length === 0) {
            document.getElementById('content-wrapper').innerHTML = `<div style="text-align: center; padding: 60px 20px; color: #9DC9FF;"><div style="font-size: 1.2rem;">No sweeps match your filters</div></div>`;
            document.getElementById('pagination').style.display = 'none';
            return;
        }

        const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
        const endIdx = startIdx + ITEMS_PER_PAGE;
        const paginatedSweeps = filtered.slice(startIdx, endIdx);

        const rows = paginatedSweeps.map(sweep => {
            const heatmap = getSweepsHeatmapStyle(sweep.usd_amount);
            const newClass = sweep.isNew ? 'new-row' : '';
            const bgStyle = `background-color: ${heatmap.bg};`;
            return `<tr class="${newClass}" style="cursor: pointer; ${bgStyle}" onclick="window.open('https://polymarket.com/event/${sweep.market_slug}', '_blank')"><td class="${heatmap.class}">${heatmap.emoji} ${formatUSD(sweep.usd_amount)}</td><td>${sweep.outcome}</td><td>${(sweep.price * 100).toFixed(1)}%</td><td style="max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${sweep.title}</td><td>${timeAgo(sweep.timestamp)}</td></tr>`;
        }).join('');

        document.getElementById('content-wrapper').innerHTML = `<table class="sweep-table"><thead><tr><th>Amount</th><th>Side</th><th>Price</th><th>Market</th><th>Time</th></tr></thead><tbody>${rows}</tbody></table>`;
        renderPagination(filtered.length);
    }

    function renderWhalesTab() {
        // Whales: sweeps >= $5000 from the last 4 hours
        const fourHoursAgo = Math.floor(Date.now() / 1000) - (4 * 60 * 60);
        const whales = sweepsData.filter(sweep => {
            return sweep.usd_amount >= 5000 && sweep.timestamp >= fourHoursAgo;
        });

        if (whales.length === 0) {
            document.getElementById('content-wrapper').innerHTML = `<div style="text-align: center; padding: 60px 20px; color: #9DC9FF;"><div style="font-size: 1.2rem;">🐋 No whale sweeps in the last 4 hours</div></div>`;
            document.getElementById('pagination').style.display = 'none';
            return;
        }

        const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
        const endIdx = startIdx + ITEMS_PER_PAGE;
        const paginated = whales.slice(startIdx, endIdx);

        const rows = paginated.map(sweep => {
            const heatmap = getSweepsHeatmapStyle(sweep.usd_amount);
            const newClass = sweep.isNew ? 'new-row' : '';
            const bgStyle = `background-color: ${heatmap.bg};`;
            return `<tr class="${newClass}" style="cursor: pointer; ${bgStyle}" onclick="window.open('https://polymarket.com/event/${sweep.market_slug}', '_blank')"><td class="${heatmap.class}">${heatmap.emoji} ${formatUSD(sweep.usd_amount)}</td><td>${sweep.outcome}</td><td>${(sweep.price * 100).toFixed(1)}%</td><td style="max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${sweep.title}</td><td>${timeAgo(sweep.timestamp)}</td></tr>`;
        }).join('');

        document.getElementById('content-wrapper').innerHTML = `<table class="sweep-table"><thead><tr><th>Amount</th><th>Side</th><th>Price</th><th>Market</th><th>Time</th></tr></thead><tbody>${rows}</tbody></table>`;
        renderPagination(whales.length);
    }

    function renderNOMarketsTab() {
        const filtered = getFilteredSweeps();
        const noSweeps = filtered.filter(s => s.outcome && s.outcome.toUpperCase() === 'NO');
        const markets = {};
        noSweeps.forEach(sweep => {
            if (!markets[sweep.market_slug]) markets[sweep.market_slug] = { title: sweep.title, slug: sweep.market_slug, volume: 0 };
            markets[sweep.market_slug].volume += sweep.usd_amount;
        });
        const sorted = Object.values(markets).sort((a, b) => b.volume - a.volume);

        if (sorted.length === 0) {
            document.getElementById('content-wrapper').innerHTML = `<div style="text-align: center; padding: 60px 20px; color: #9DC9FF;"><div style="font-size: 1.2rem;">No NO markets found</div></div>`;
            document.getElementById('pagination').style.display = 'none';
            return;
        }

        const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
        const endIdx = startIdx + ITEMS_PER_PAGE;
        const paginated = sorted.slice(startIdx, endIdx);

        const rows = paginated.map(m => {
            const heatmap = getHeatmapStyle(m.volume);
            const bgStyle = `background-color: ${heatmap.bg};`;
            return `<tr style="cursor: pointer; ${bgStyle}" onclick="window.open('https://polymarket.com/event/${m.slug}', '_blank')"><td class="${heatmap.class}" style="width: 150px;">${heatmap.emoji} ${formatUSD(m.volume)}</td><td style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${m.title}</td></tr>`;
        }).join('');

        document.getElementById('content-wrapper').innerHTML = `<table class="sweep-table"><thead><tr><th style="width: 150px;">NO Volume</th><th>Market</th></tr></thead><tbody>${rows}</tbody></table>`;
        renderPagination(sorted.length);
    }

    function renderEdgeMarketsTab() {
        const filtered = getFilteredSweeps();
        const markets = {};
        filtered.forEach(sweep => {
            if (!markets[sweep.market_slug]) markets[sweep.market_slug] = { title: sweep.title, slug: sweep.market_slug, price: sweep.price, timestamp: sweep.timestamp };
            else if (sweep.timestamp > markets[sweep.market_slug].timestamp) { markets[sweep.market_slug].price = sweep.price; markets[sweep.market_slug].timestamp = sweep.timestamp; }
        });
        const edge = Object.values(markets).filter(m => m.price > 0.15 && m.price < 0.85).sort((a, b) => a.price - b.price);

        if (edge.length === 0) {
            document.getElementById('content-wrapper').innerHTML = `<div style="text-align: center; padding: 60px 20px; color: #9DC9FF;"><div style="font-size: 1.2rem;">No edge markets found</div></div>`;
            document.getElementById('pagination').style.display = 'none';
            return;
        }

        const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
        const endIdx = startIdx + ITEMS_PER_PAGE;
        const paginated = edge.slice(startIdx, endIdx);

        const rows = paginated.map(m => `<tr style="cursor: pointer;" onclick="window.open('https://polymarket.com/event/${m.slug}', '_blank')"><td style="color: #22D3EE; width: 150px;">${(m.price * 100).toFixed(1)}%</td><td style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${m.title}</td></tr>`).join('');

        document.getElementById('content-wrapper').innerHTML = `<table class="sweep-table"><thead><tr><th style="width: 150px;">Current Price</th><th>Market</th></tr></thead><tbody>${rows}</tbody></table>`;
        renderPagination(edge.length);
    }

    function renderClosingSoonTab() {
        if (expiringData.length === 0) {
            document.getElementById('content-wrapper').innerHTML = `<div style="text-align: center; padding: 60px 20px; color: #9DC9FF;"><div style="font-size: 1.2rem;">No markets closing soon</div></div>`;
            document.getElementById('pagination').style.display = 'none';
            return;
        }

        const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
        const endIdx = startIdx + ITEMS_PER_PAGE;
        const paginated = expiringData.slice(startIdx, endIdx);

        const rows = paginated.map(m => {
            const hoursColor = m.hours_until < 6 ? '#F87171' : m.hours_until < 24 ? '#FACC15' : '#9CA3AF';
            return `<tr style="cursor: pointer;" onclick="window.open('https://polymarket.com/event/${m.market_slug}', '_blank')"><td style="color: ${hoursColor}; width: 120px;">${m.hours_until.toFixed(1)}h</td><td style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${m.title}</td></tr>`;
        }).join('');

        document.getElementById('content-wrapper').innerHTML = `<table class="sweep-table"><thead><tr><th style="width: 120px;">Expires In</th><th>Market</th></tr></thead><tbody>${rows}</tbody></table>`;
        renderPagination(expiringData.length);
    }

    function renderClustersTab() {
        const filtered = getFilteredSweeps();
        const markets = {};
        filtered.forEach(sweep => {
            if (!markets[sweep.market_slug]) markets[sweep.market_slug] = { title: sweep.title, slug: sweep.market_slug, count: 0, volume: 0 };
            markets[sweep.market_slug].count++;
            markets[sweep.market_slug].volume += sweep.usd_amount;
        });
        const clusters = Object.values(markets).filter(m => m.count >= 2).sort((a, b) => b.count - a.count);

        if (clusters.length === 0) {
            document.getElementById('content-wrapper').innerHTML = `<div style="text-align: center; padding: 60px 20px; color: #9DC9FF;"><div style="font-size: 1.2rem;">No clusters found</div></div>`;
            document.getElementById('pagination').style.display = 'none';
            return;
        }

        const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
        const endIdx = startIdx + ITEMS_PER_PAGE;
        const paginated = clusters.slice(startIdx, endIdx);

        const rows = paginated.map(m => {
            const heatmap = getHeatmapStyle(m.volume);
            const bgStyle = `background-color: ${heatmap.bg};`;
            return `<tr style="cursor: pointer; ${bgStyle}" onclick="window.open('https://polymarket.com/event/${m.slug}', '_blank')"><td style="color: #C084FC;">🔥 ${m.count}</td><td class="${heatmap.class}">${heatmap.emoji} ${formatUSD(m.volume)}</td><td style="max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${m.title}</td></tr>`;
        }).join('');

        document.getElementById('content-wrapper').innerHTML = `<table class="sweep-table"><thead><tr><th>Sweeps</th><th>Volume</th><th>Market</th></tr></thead><tbody>${rows}</tbody></table>`;
        renderPagination(clusters.length);
    }

    document.querySelectorAll('.dashboard-tab').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.dashboard-tab').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            renderTab(this.dataset.tab);
        });
    });

    ['filter-min-amount', 'filter-ignore-sports', 'filter-ignore-crypto'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('change', () => renderTab(activeTab));
            el.addEventListener('input', () => renderTab(activeTab));
        }
    });

    document.getElementById('content-wrapper').addEventListener('mouseenter', () => {
        isHovering = true;
        document.getElementById('live-indicator').style.display = 'none';
        document.getElementById('pause-indicator').style.display = 'inline-flex';
    });
    document.getElementById('content-wrapper').addEventListener('mouseleave', () => {
        isHovering = false;
        document.getElementById('live-indicator').style.display = 'inline-flex';
        document.getElementById('pause-indicator').style.display = 'none';
    });

    fetchData();
    setInterval(fetchData, 5000);
})();
