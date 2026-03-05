/**
 * Gallery.js — Client-side rendering engine for the photo gallery.
 * Handles grid rendering, sorting, shuffling, tag filtering, searching,
 * and lightbox display from an in-memory photo array.
 */
const Gallery = (function () {
    'use strict';

    let allPhotos = [];           // master copy (default desc order)
    let currentPhotos = [];       // filtered/sorted subset currently displayed
    let currentSort = 'desc';
    let currentTag = '';
    let currentQuery = '';
    let adminMode = false;

    /* ── Initialization ── */
    function init(photos, options = {}) {
        allPhotos = photos;
        adminMode = options.adminMode || false;
        applyFiltersAndRender();
    }

    /* ── Filtering & Sorting Pipeline ── */
    function applyFiltersAndRender() {
        let filtered = allPhotos.slice();

        // Apply tag filter
        if (currentTag) {
            filtered = filtered.filter(p =>
                p.tags && p.tags.some(t => t.toLowerCase() === currentTag.toLowerCase())
            );
        }

        // Apply search filter
        if (currentQuery) {
            const q = currentQuery.toLowerCase();
            filtered = filtered.filter(p =>
                p.filename.toLowerCase().includes(q) ||
                p.title.toLowerCase().includes(q) ||
                p.description.toLowerCase().includes(q) ||
                p.location.toLowerCase().includes(q) ||
                (p.tags && p.tags.some(t => t.toLowerCase().includes(q)))
            );
        }

        // Apply sort
        if (currentSort === 'shuffle') {
            shuffleArray(filtered);
        } else {
            filtered.sort((a, b) => {
                const dateA = a.taken_at || a.uploaded_at || '';
                const dateB = b.taken_at || b.uploaded_at || '';
                return currentSort === 'asc'
                    ? dateA.localeCompare(dateB)
                    : dateB.localeCompare(dateA);
            });
        }

        currentPhotos = filtered;
        renderGrid(filtered);
        updatePhotoCount(filtered.length);
    }

    /* ── Grid Rendering ── */
    function renderGrid(photos) {
        const container = document.getElementById('photo-grid');
        if (!container) return;

        if (photos.length === 0) {
            container.innerHTML =
                '<div class="empty-state">' +
                '  <p class="empty-icon">⬜</p>' +
                '  <p class="empty-title">No photos found</p>' +
                '  <p class="empty-hint">Try adjusting your filters or search.</p>' +
                '</div>';
            destroyTimeScrubber();
            return;
        }

        // Group by year
        const groups = {};
        if (currentSort === 'shuffle') {
            groups['Shuffled'] = photos;
        } else {
            photos.forEach(p => {
                const dt = p.taken_at || p.uploaded_at;
                const year = dt ? new Date(dt).getFullYear() : 'Unknown';
                if (!groups[year]) groups[year] = [];
                groups[year].push(p);
            });
        }

        let html = '<div class="gallery-content"><div class="timeline-sections">';

        const years = Object.keys(groups);
        years.forEach(year => {
            const yearPhotos = groups[year];
            html += '<div class="year-section" id="' + year + '" style="margin-top: 2rem; scroll-margin-top: 80px;">';
            html += '<h2 class="year-header" style="font-family: var(--font-serif); font-size: 1.5rem; color: var(--text-secondary); margin-bottom: 0.5rem; opacity: 0.8;">' + year + '</h2>';
            html += '<div class="masonry-grid">';

            yearPhotos.forEach(photo => {
                html += '<div class="photo-card" onclick="Gallery.openLightbox(' + photo.id + ')" role="button" tabindex="0" aria-label="' + escapeAttr(photo.title) + '">';
                html += '<div class="photo-thumb">';
                html += '<img src="' + escapeAttr(photo.image_url) + '" alt="' + escapeAttr(photo.title) + '" loading="lazy">';
                html += '<div class="photo-overlay">';
                html += '<span class="overlay-title">' + escapeHtml(photo.title) + '</span>';
                if (photo.location) {
                    html += '<span class="overlay-location">' + escapeHtml(photo.location) + '</span>';
                }
                html += '</div></div></div>';
            });

            html += '</div></div>';
        });

        html += '</div>';

        // Time scrubber
        if (currentSort !== 'shuffle' && years.length > 1) {
            html += buildTimeScrubber(years);
        }

        html += '</div>';
        container.innerHTML = html;

        // Initialize scrubber behavior
        if (currentSort !== 'shuffle' && years.length > 1) {
            initTimeScrubber();
        }
    }

    /* ── Time Scrubber ── */
    function buildTimeScrubber(years) {
        let html = '<div class="time-scrubber" id="time-scrubber" style="position: fixed; right: 1rem; top: 50%; transform: translateY(-50%); display: flex; flex-direction: column; gap: 8px; z-index: 100; background: rgba(0,0,0,0.4); padding: 10px 5px; border-radius: 20px; backdrop-filter: blur(8px); transition: opacity 0.4s ease, visibility 0.4s ease;">';
        years.forEach(year => {
            html += '<a href="#' + year + '" class="scrubber-link" style="color: var(--text-muted); font-size: 0.75rem; writing-mode: vertical-rl; text-orientation: mixed; transition: color 0.2s; text-decoration: none; display: block; text-align: center; font-weight: 500;">' + year + '</a>';
        });
        html += '</div>';
        return html;
    }

    let scrubberTimer = null;
    function initTimeScrubber() {
        const scrubber = document.getElementById('time-scrubber');
        if (!scrubber) return;

        function hideScrubber() { scrubber.style.opacity = '0'; scrubber.style.pointerEvents = 'none'; }
        function showScrubber() { scrubber.style.opacity = '1'; scrubber.style.pointerEvents = 'auto'; }
        function resetTimer() {
            showScrubber();
            clearTimeout(scrubberTimer);
            scrubberTimer = setTimeout(hideScrubber, 3000);
        }

        resetTimer();

        document.addEventListener('touchstart', function handler(e) {
            if (e.target.closest('.time-scrubber') || document.body.classList.contains('modal-open')) return;
            if (scrubber.style.opacity === '0') { resetTimer(); } else { hideScrubber(); clearTimeout(scrubberTimer); }
        }, { passive: true });

        document.addEventListener('pointermove', function handler(e) {
            if (e.pointerType !== 'mouse' || document.body.classList.contains('modal-open')) return;
            resetTimer();
        }, { passive: true });

        window.addEventListener('scroll', function handler() {
            if (!document.body.classList.contains('modal-open')) resetTimer();
        }, { passive: true });
    }

    function destroyTimeScrubber() {
        const existing = document.getElementById('time-scrubber');
        if (existing) existing.remove();
    }

    /* ── Lightbox ── */
    function openLightbox(photoId) {
        const idx = currentPhotos.findIndex(p => p.id === photoId);
        if (idx === -1) return;
        renderLightbox(idx);
    }

    function renderLightbox(idx) {
        const photo = currentPhotos[idx];
        if (!photo) return;

        const prevId = idx > 0 ? currentPhotos[idx - 1].id : null;
        const nextId = idx < currentPhotos.length - 1 ? currentPhotos[idx + 1].id : null;

        let html = '<div class="lightbox" id="lightbox-inner" data-photo-id="' + photo.id + '" data-filename="' + escapeAttr(photo.filename) + '" data-prev-id="' + (prevId || '') + '" data-next-id="' + (nextId || '') + '" data-sort="' + currentSort + '">';

        // Controls
        html += '<div class="lightbox-controls">';
        html += '<button class="lightbox-close" onclick="closeModal()" aria-label="Close">&#10005;</button>';
        html += '<button class="lightbox-close" onclick="closeModal()" aria-label="Close">&#10005;</button>';

        if (prevId !== null) {
            html += '<button class="lightbox-arrow lightbox-arrow--prev" onclick="Gallery.navigateLightbox(\'prev\')" aria-label="Previous photo">&#8592;</button>';
        }
        if (nextId !== null) {
            html += '<button class="lightbox-arrow lightbox-arrow--next" onclick="Gallery.navigateLightbox(\'next\')" aria-label="Next photo">&#8594;</button>';
        }
        html += '</div>';

        // Image
        html += '<div class="lightbox-image">';
        html += '<img src="' + escapeAttr(photo.image_url) + '" alt="' + escapeAttr(photo.title) + '">';
        html += '</div>';

        // Meta
        html += '<div class="lightbox-meta">';
        html += '<h2 class="meta-title">' + escapeHtml(photo.title) + '</h2>';
        if (photo.description) {
            html += '<p class="meta-description">' + escapeHtml(photo.description) + '</p>';
        }
        html += '<div class="meta-fields">';
        if (photo.location) {
            html += '<div class="meta-field"><span class="meta-label">Location</span><span class="meta-value">' + escapeHtml(photo.location) + '</span></div>';
        }
        if (photo.taken_at) {
            const dateStr = formatDate(photo.taken_at);
            html += '<div class="meta-field"><span class="meta-label">Date</span><span class="meta-value">' + dateStr + '</span></div>';
        }
        if (photo.tags && photo.tags.length > 0) {
            html += '<div class="meta-field"><span class="meta-label">Tags</span><div class="meta-tags">';
            photo.tags.forEach(tag => {
                html += '<a href="/?tag=' + encodeURIComponent(tag) + '" class="tag" onclick="event.preventDefault(); Gallery.setTag(\'' + escapeAttr(tag) + '\'); closeModal();">' + escapeHtml(tag) + '</a>';
            });
            html += '</div></div>';
        }
        html += '</div>';
        html += '<p class="meta-filename">' + escapeHtml(photo.filename) + '</p>';

        // Admin actions (kept as HTMX since they need server interaction)
        if (adminMode) {
            html += '<div class="admin-actions" style="display: flex; gap: 1rem; margin-top: 1.5rem; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 1.5rem;">';
            html += '<button class="btn btn-secondary" hx-get="/photo/' + photo.id + '/edit" hx-target="#modal-content" hx-swap="innerHTML" style="flex: 1; padding: 0.5rem; background: rgba(255,255,255,0.1); border: none; border-radius: 4px; color: white; cursor: pointer;">Edit</button>';
            html += '<button class="btn btn-danger" hx-delete="/photo/' + photo.id + '" hx-confirm="Are you sure you want to delete this photo?" style="flex: 1; padding: 0.5rem; background: rgba(255,50,50,0.2); border: 1px solid rgba(255,50,50,0.5); border-radius: 4px; color: white; cursor: pointer;">Delete</button>';
            html += '</div>';
        }

        html += '</div></div>';

        const modalContent = document.getElementById('modal-content');
        modalContent.innerHTML = html;

        // Process HTMX for admin buttons if present
        if (adminMode && typeof htmx !== 'undefined') {
            htmx.process(modalContent);
        }

        // Open the modal
        const modal = document.getElementById('photo-modal');
        modal.classList.add('active');
        document.body.classList.add('modal-open');

        // Reset auto-hide timer
        if (typeof resetControlTimer === 'function') {
            resetControlTimer();
        }

        // Update URL
        const url = new URL(window.location);
        const identifier = photo.filename || photo.id;
        if (url.searchParams.get('p') !== String(identifier)) {
            url.searchParams.set('p', identifier);
            window.history.pushState({ modalOpen: true, photoId: identifier }, '', url);
        }
    }

    function navigateLightbox(direction) {
        const lb = document.getElementById('lightbox-inner');
        if (!lb) return;

        const currentId = parseInt(lb.dataset.photoId);
        const idx = currentPhotos.findIndex(p => p.id === currentId);
        if (idx === -1) return;

        const newIdx = direction === 'prev' ? idx - 1 : idx + 1;
        if (newIdx < 0 || newIdx >= currentPhotos.length) return;

        renderLightbox(newIdx);
    }

    function openLightboxByFilename(filename) {
        // Try exact match first
        let idx = currentPhotos.findIndex(p => p.filename === filename);
        // Try stem match (without extension)
        if (idx === -1) {
            idx = currentPhotos.findIndex(p => p.filename.startsWith(filename));
        }
        if (idx === -1) return;
        renderLightbox(idx);
    }

    /* ── Public API for search/sort/tag ── */
    function search(query) {
        currentQuery = query.trim();
        if (currentQuery) {
            clearTagUI();
            currentTag = '';
        }
        applyFiltersAndRender();
    }

    function sort(mode) {
        currentSort = mode;
        applyFiltersAndRender();
    }

    function setTag(tagName) {
        currentTag = tagName;
        currentQuery = '';

        // Update UI
        const searchInput = document.querySelector('.search-input');
        if (searchInput) searchInput.value = '';

        const indicator = document.getElementById('active-tag-indicator');
        const text = document.getElementById('active-tag-text');
        if (indicator && text) {
            text.textContent = tagName;
            indicator.style.display = 'inline-flex';
        }

        // Update URL
        const url = new URL(window.location);
        url.searchParams.set('tag', tagName);
        url.searchParams.delete('q');
        url.searchParams.delete('p');
        window.history.pushState({ tag: tagName }, '', url);

        applyFiltersAndRender();
    }

    function clearTag() {
        if (!currentTag) return;
        currentTag = '';
        clearTagUI();

        // Update URL
        const url = new URL(window.location);
        url.searchParams.delete('tag');
        url.searchParams.delete('p');
        window.history.pushState({ tag: null }, '', url);

        applyFiltersAndRender();
    }

    function clearTagUI() {
        const tagInput = document.getElementById('tag-input');
        const indicator = document.getElementById('active-tag-indicator');
        if (tagInput) tagInput.value = '';
        if (indicator) indicator.style.display = 'none';
    }

    /* ── Photo Count ── */
    function updatePhotoCount(count) {
        const el = document.getElementById('photo-count');
        if (el) {
            el.textContent = count + ' photo' + (count !== 1 ? 's' : '');
        }
    }

    /* ── Helpers ── */
    function shuffleArray(arr) {
        for (let i = arr.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [arr[i], arr[j]] = [arr[j], arr[i]];
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function escapeAttr(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function formatDate(isoString) {
        const d = new Date(isoString);
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return months[d.getMonth()] + ' ' + String(d.getDate()).padStart(2, '0') + ', ' + d.getFullYear();
    }

    /* ── Public Interface ── */
    return {
        init,
        openLightbox,
        openLightboxByFilename,
        navigateLightbox,
        search,
        sort,
        setTag,
        clearTag,
        getCurrentSort: () => currentSort,
        getCurrentPhotos: () => currentPhotos,
    };
})();
