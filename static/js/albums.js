/**
 * Albums.js — Client-side album grid renderer.
 * Groups photos by location and renders album cards with cover images.
 */
const Albums = (function () {
    'use strict';

    const IMAGE_BASE_URL = window.IMAGE_BASE_URL;
    let observer = null;

    function init(photos) {
        const albums = buildAlbums(photos);
        renderGrid(albums);
    }

    /* ── Build album data from photos ── */
    function buildAlbums(photos) {
        const map = {};

        photos.forEach(p => {
            const loc = (p.location || '').trim();
            if (!loc) return;

            if (!map[loc]) {
                map[loc] = { location: loc, count: 0, cover: null, newestDate: '' };
            }
            map[loc].count++;

            // Pick the most recent photo as cover
            const date = p.taken_at || p.uploaded_at || '';
            if (date > map[loc].newestDate) {
                map[loc].newestDate = date;
                map[loc].cover = p.filename;
            }
        });

        // Sort albums by count descending
        return Object.values(map).sort((a, b) => b.count - a.count);
    }

    /* ── Render album grid ── */
    function renderGrid(albums) {
        const container = document.getElementById('album-grid');
        if (!container) return;

        // Update count
        const countEl = document.getElementById('album-count');
        if (countEl) {
            countEl.textContent = albums.length + ' album' + (albums.length !== 1 ? 's' : '');
        }

        if (albums.length === 0) {
            container.innerHTML =
                '<div class="empty-state">' +
                '  <p class="empty-icon">📁</p>' +
                '  <p class="empty-title">No albums yet</p>' +
                '  <p class="empty-hint">Add locations to your photos to create albums.</p>' +
                '</div>';
            return;
        }

        let html = '<div class="album-grid">';

        albums.forEach(album => {
            const href = '/?city=' + encodeURIComponent(album.location);
            html += '<a href="' + escapeAttr(href) + '" class="album-card" data-cover="' + escapeAttr(album.cover) + '">';
            html += '<div class="album-cover-wrapper">';
            html += '<img class="album-cover" alt="' + escapeAttr(album.location) + '" loading="lazy">';
            html += '</div>';
            html += '<div class="album-overlay">';
            html += '<span class="album-name">' + escapeHtml(album.location) + '</span>';
            html += '<span class="album-count">' + album.count + ' photo' + (album.count !== 1 ? 's' : '') + '</span>';
            html += '</div>';
            html += '</a>';
        });

        html += '</div>';
        container.innerHTML = html;

        // Setup lazy loading for cover images
        setupObserver();
    }

    /* ── Lazy loading for album covers ── */
    function setupObserver() {
        if (observer) observer.disconnect();

        observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) return;

                const card = entry.target;
                const cover = card.dataset.cover;
                if (!cover) return;

                const img = card.querySelector('.album-cover');
                if (img && !img.src) {
                    img.src = IMAGE_BASE_URL + cover;
                }

                observer.unobserve(card);
            });
        }, { rootMargin: '200px 0px' });

        document.querySelectorAll('.album-card').forEach(card => {
            observer.observe(card);
        });
    }

    /* ── Helpers ── */
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

    return { init };
})();
