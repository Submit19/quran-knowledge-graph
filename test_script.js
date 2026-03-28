
    // ── marked config ────────────────────────────────────────────────────────────
    marked.use({ breaks: true, gfm: true });

    // ── examples ─────────────────────────────────────────────────────────────────
    const EXAMPLES = [
      "What does the Quran say about the covenant with Abraham?",
      "What is the significance of the number 19?",
      "How are prayer and remembrance connected?",
      "What does the Quran say about the role of Jesus?",
      "Show me the thematic path between verse 2:255 and 112:1",
      "Explore Surah 36 (Ya-Sin) and its connections",
    ];
    const examplesEl = document.getElementById('examples');
    EXAMPLES.forEach(ex => {
      const btn = document.createElement('button');
      btn.className = 'ex-btn'; btn.textContent = ex;
      btn.onclick = () => { document.getElementById('input').value = ex; sendMessage(); };
      examplesEl.appendChild(btn);
    });

    // ════════════════════════════════════════════════════════════════════════════
    // 3D GRAPH
    // ════════════════════════════════════════════════════════════════════════════
    const graphPanel = document.getElementById('graph-panel');

    // ── colour helpers ───────────────────────────────────────────────────────────
    const C_VERSE_ACTIVE   = new THREE.Color('#6ee7b7');
    const C_VERSE_CONV     = new THREE.Color('#0d9488');   // in conversation, not active
    const C_VERSE_IDLE     = new THREE.Color('#0f4c3a');   // all other verses (dim)
    const C_KEYWORD_ACTIVE = new THREE.Color('#fde68a');
    const C_KEYWORD_IDLE   = new THREE.Color('#d97706');

    function nodeBaseColor(node) {
      if (node.type === 'keyword') return node.active ? C_KEYWORD_ACTIVE : C_KEYWORD_IDLE;
      if (node.active)       return C_VERSE_ACTIVE;
      if (node.inConv)       return C_VERSE_CONV;
      return C_VERSE_IDLE;
    }

    // ── sprite factory ───────────────────────────────────────────────────────────
    function makeSprite(text, type) {
      const w = 256, h = 52;
      const canvas = document.createElement('canvas');
      canvas.width = w; canvas.height = h;
      const ctx = canvas.getContext('2d');
      ctx.font = 'bold 24px monospace';
      ctx.fillStyle = type === 'keyword' ? '#fde68a' : '#a7f3d0';
      ctx.shadowColor = '#000'; ctx.shadowBlur = 5;
      ctx.fillText(text, 6, 38);
      const tex = new THREE.CanvasTexture(canvas);
      const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false });
      const sprite = new THREE.Sprite(mat);
      sprite.scale.set(w / 12, h / 12, 1);
      sprite.position.set(0, 7, 0);
      sprite.name = 'label';
      sprite.visible = false;
      return sprite;
    }

    // ── build Three.js object for a node ────────────────────────────────────────
    function buildNodeObj(node) {
      // Base verses (not yet touched by conversation): tiny dim sphere, no sprite
      if (node.type === 'verse' && !node.inConv && !node.active) {
        const geo  = new THREE.SphereGeometry(1.2, 5, 5);
        const col  = C_VERSE_IDLE.clone();
        const mat  = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.45 });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.name  = 'sphere';
        const g    = new THREE.Group();
        g.add(mesh);
        node.__obj = g;
        return g;
      }

      // Conversation / keyword nodes: full sphere + optional aura + label
      const isKw = node.type === 'keyword';
      const r    = isKw ? 2.5 : 4;
      const col  = nodeBaseColor(node);
      const group = new THREE.Group();

      const geo = new THREE.SphereGeometry(r, 14, 14);
      const mat = new THREE.MeshPhongMaterial({
        color: col.clone(), emissive: col.clone(),
        emissiveIntensity: node.active ? 0.85 : 0.15,
        transparent: true, opacity: node.active ? 1.0 : 0.75,
        shininess: 90,
      });
      const sphere = new THREE.Mesh(geo, mat);
      sphere.name = 'sphere';
      group.add(sphere);

      if (node.active) {
        const ag = new THREE.SphereGeometry(r * 2.4, 8, 8);
        const am = new THREE.MeshBasicMaterial({
          color: col.clone(), transparent: true, opacity: 0.10, side: THREE.BackSide,
        });
        const aura = new THREE.Mesh(ag, am);
        aura.name = 'aura';
        group.add(aura);
      }

      const sprite = makeSprite(node.label, node.type);
      // Labels always visible for active and conversation nodes
      sprite.visible = true;
      group.add(sprite);
      node.__obj = group;
      return group;
    }

    // ── refresh an existing node object in-place ─────────────────────────────────
    let hoveredNode = null;

    function refreshNode(node) {
      if (!node.__obj) return;

      // If this was a dim base node but is now in conversation, rebuild it properly
      const sphere = node.__obj.getObjectByName('sphere');
      const isFullNode = sphere && sphere.type === 'Mesh' &&
                         sphere.material.type === 'MeshPhongMaterial';
      const needsUpgrade = (node.inConv || node.active) &&
                           sphere && sphere.material.type === 'MeshBasicMaterial';

      if (needsUpgrade) {
        // Replace the simple mesh with the full node object
        // Remove all children
        while (node.__obj.children.length) {
          const c = node.__obj.children[0];
          node.__obj.remove(c);
          if (c.geometry) c.geometry.dispose();
          if (c.material) c.material.dispose();
        }
        // Re-add full geometry
        const isKw = node.type === 'keyword';
        const r    = isKw ? 2.5 : 4;
        const col  = nodeBaseColor(node);
        const geo  = new THREE.SphereGeometry(r, 14, 14);
        const mat  = new THREE.MeshPhongMaterial({
          color: col.clone(), emissive: col.clone(),
          emissiveIntensity: node.active ? 0.85 : 0.15,
          transparent: true, opacity: node.active ? 1.0 : 0.75,
          shininess: 90,
        });
        const newSphere = new THREE.Mesh(geo, mat);
        newSphere.name = 'sphere';
        node.__obj.add(newSphere);
        const sp = makeSprite(node.label, node.type);
        sp.visible = true;
        node.__obj.add(sp);
        if (node.active) {
          const ag = new THREE.SphereGeometry(r * 2.4, 8, 8);
          const am = new THREE.MeshBasicMaterial({
            color: col.clone(), transparent: true, opacity: 0.10, side: THREE.BackSide,
          });
          const aura = new THREE.Mesh(ag, am); aura.name = 'aura';
          node.__obj.add(aura);
        }
        return;
      }

      const col = nodeBaseColor(node);
      if (sphere) {
        sphere.material.color.copy(col);
        if (sphere.material.emissive) {
          sphere.material.emissive.copy(col);
          sphere.material.emissiveIntensity = node.active ? 0.85 : 0.15;
        }
        sphere.material.opacity = node.active ? 1.0 : (node.inConv ? 0.75 : 0.45);
        sphere.material.needsUpdate = true;
      }

      // aura
      let aura = node.__obj.getObjectByName('aura');
      if (node.active && !aura) {
        const r  = node.type === 'keyword' ? 2.5 : 4;
        const ag = new THREE.SphereGeometry(r * 2.4, 8, 8);
        const am = new THREE.MeshBasicMaterial({
          color: col.clone(), transparent: true, opacity: 0.10, side: THREE.BackSide,
        });
        aura = new THREE.Mesh(ag, am); aura.name = 'aura';
        node.__obj.add(aura);
      } else if (!node.active && aura) {
        node.__obj.remove(aura);
        aura.geometry.dispose(); aura.material.dispose();
      }

      // label: always visible for conv/active, visible on hover too
      const label = node.__obj.getObjectByName('label');
      if (label) {
        label.visible = node.active || node.inConv || node === hoveredNode;
      }
    }

    // ── pre-compute galaxy positions ─────────────────────────────────────────────
    // Each surah gets a center on a fibonacci sphere (radius 600).
    // Each surah's verses form a ring in the plane perpendicular to the radius.
    const GALAXY_POSITIONS = {};

    function fibSphere(i, n, R) {
      const phi   = Math.acos(1 - 2 * (i + 0.5) / n);
      const theta = Math.PI * (1 + Math.sqrt(5)) * i;
      return new THREE.Vector3(
        R * Math.sin(phi) * Math.cos(theta),
        R * Math.cos(phi),
        R * Math.sin(phi) * Math.sin(theta)
      );
    }

    // Two vectors perpendicular to 'dir'
    function perpFrame(dir) {
      const up = Math.abs(dir.y) < 0.9 ? new THREE.Vector3(0, 1, 0)
                                        : new THREE.Vector3(1, 0, 0);
      const u  = new THREE.Vector3().crossVectors(up, dir).normalize();
      const v  = new THREE.Vector3().crossVectors(dir, u).normalize();
      return { u, v };
    }

    function buildGalaxyPositions(verses) {
      // Group by surah
      const bySurah = {};
      for (const v of verses) {
        if (!bySurah[v.surah]) bySurah[v.surah] = [];
        bySurah[v.surah].push(v.id);
      }
      const surahNums = Object.keys(bySurah).map(Number).sort((a, b) => a - b);

      surahNums.forEach((sNum, si) => {
        const center = fibSphere(si, 114, 600);
        const dir    = center.clone().normalize();
        const { u, v } = perpFrame(dir);
        const ids    = bySurah[sNum];
        const n      = ids.length;
        // Ring radius scales with verse count (min 20, max 90)
        const ringR  = Math.min(20 + n * 0.55, 90);

        ids.forEach((id, vi) => {
          const angle = (vi / n) * 2 * Math.PI;
          const pos   = new THREE.Vector3()
            .addScaledVector(center, 1)
            .addScaledVector(u, Math.cos(angle) * ringR)
            .addScaledVector(v, Math.sin(angle) * ringR);
          GALAXY_POSITIONS[id] = pos;
        });
      });
    }

    // ── surah colour palette (hue spread over 114 surahs) ───────────────────────
    function surahColor(surahNum) {
      const hue = ((surahNum - 1) / 114) * 360;
      return new THREE.Color().setHSL(hue / 360, 0.7, 0.18);  // dim version
    }

    // ── Graph instance ───────────────────────────────────────────────────────────
    const Graph = ForceGraph3D({ antialias: true, alpha: true })
      (graphPanel)
      .width(graphPanel.clientWidth)
      .height(graphPanel.clientHeight)
      .backgroundColor('#060a14')
      .showNavInfo(false)
      .nodeThreeObject(buildNodeObj)
      .nodeThreeObjectExtend(false)
      .nodeLabel(() => '')
      .linkColor(link => link.type === 'mentions' ? '#78350f' : '#164e63')
      .linkWidth(link => link.type === 'related' ? 0.8 : 0.4)
      .linkOpacity(0.6)
      .linkDirectionalParticles(link => link.type === 'related' ? 3 : 0)
      .linkDirectionalParticleWidth(1.4)
      .linkDirectionalParticleSpeed(0.005)
      .d3AlphaDecay(0.02)
      .d3VelocityDecay(0.4)
      .onNodeHover(node => {
        if (hoveredNode && hoveredNode !== node) refreshNode(hoveredNode);
        hoveredNode = node || null;
        if (hoveredNode) refreshNode(hoveredNode);
        graphPanel.style.cursor = node ? 'pointer' : 'default';
      })
      .onNodeClick(node => {
        if (!node) return;
        const infoEl  = document.getElementById('node-info');
        const titleEl = document.getElementById('node-info-title');
        const bodyEl  = document.getElementById('node-info-body');
        if (node.type === 'verse') {
          titleEl.textContent = `[${node.verseId}]  ${node.surahName || ''}`;
          bodyEl.textContent  = node.text || '(no text cached — ask Claude about this verse)';
        } else {
          titleEl.textContent = `Keyword: ${node.label}`;
          bodyEl.textContent  = 'Click a verse node to read its text.';
        }
        infoEl.style.display = 'block';
      })
      .onEngineStop(() => {
        // Pin all settled nodes
        Graph.graphData().nodes.forEach(node => {
          if (node.x !== undefined && !node.fx) {
            node.fx = node.x; node.fy = node.y; node.fz = node.z;
          }
        });
      });

    // Prevent page scroll when over the graph
    graphPanel.addEventListener('wheel', e => e.preventDefault(), { passive: false });

    // Keep graph sized to panel
    new ResizeObserver(() => {
      Graph.width(graphPanel.clientWidth).height(graphPanel.clientHeight);
    }).observe(graphPanel);

    // ── graph state ──────────────────────────────────────────────────────────────
    const gState = {
      nodeMap:   {},
      linkKeys:  new Set(),
      activeIds: new Set(),
    };

    // Start graph empty — nodes appear as Claude explores
    Graph.graphData({ nodes: [], links: [] });
    document.getElementById('graph-loading').style.display = 'none';
    Graph.cameraPosition({ x: 0, y: 0, z: 1400 }, { x: 0, y: 0, z: 0 }, 1000);

    // ── apply conversation graph update ──────────────────────────────────────────
    function applyGraphUpdate(update) {
      // Deactivate previous active nodes
      gState.activeIds.forEach(id => {
        const n = gState.nodeMap[id];
        if (n) { n.active = false; refreshNode(n); }
      });
      gState.activeIds.clear();

      const existing = Graph.graphData();
      const newLinks = [];

      for (const n of update.nodes) {
        const en = gState.nodeMap[n.id];
        if (en) {
          if (n.text)      en.text      = n.text;
          if (n.surahName) en.surahName = n.surahName;
          if (!en.inConv) { en.inConv = true; refreshNode(en); }
        } else {
          gState.nodeMap[n.id] = n;
        }
      }

      const existIds = new Set(existing.nodes.map(n => n.id));
      const newNodes = update.nodes.filter(n => !existIds.has(n.id));

      for (const l of update.links) {
        const key = `${l.source}>${l.target}`;
        if (!gState.linkKeys.has(key)) { gState.linkKeys.add(key); newLinks.push(l); }
      }

      if (newNodes.length || newLinks.length) {
        Graph.graphData({
          nodes: [...existing.nodes, ...newNodes],
          links: [...existing.links, ...newLinks],
        });
      }

      setTimeout(() => {
        for (const id of update.active) {
          gState.activeIds.add(id);
          const n = gState.nodeMap[id] || Graph.graphData().nodes.find(n => n.id === id);
          if (n) { n.active = true; n.inConv = true; refreshNode(n); }
        }
      }, 80);
    }

    // ════════════════════════════════════════════════════════════════════════════
    // WASD CAMERA MOVEMENT
    // ════════════════════════════════════════════════════════════════════════════
    const keys = {};
    const MOVE_SPEED = 8;

    document.addEventListener('keydown', e => {
      keys[e.key.toLowerCase()] = true;
      // Don't steal keys when typing in the input box
      if (document.activeElement === document.getElementById('input')) return;
      if (['w','a','s','d','q','e'].includes(e.key.toLowerCase())) e.preventDefault();
    });
    document.addEventListener('keyup',   e => { keys[e.key.toLowerCase()] = false; });

    // Focus graph panel on click so WASD works without extra click
    graphPanel.addEventListener('click', () => graphPanel.focus());
    graphPanel.setAttribute('tabindex', '0');

    function animateWASD() {
      requestAnimationFrame(animateWASD);

      const active = keys['w'] || keys['s'] || keys['a'] || keys['d'] || keys['q'] || keys['e'];
      if (!active) return;
      if (document.activeElement === document.getElementById('input')) return;

      const cam = Graph.camera();
      if (!cam) return;

      // Forward vector (camera direction, projected — keep Y for free-fly)
      const dir = new THREE.Vector3();
      cam.getWorldDirection(dir);

      const right = new THREE.Vector3();
      right.crossVectors(dir, cam.up).normalize();

      const up = new THREE.Vector3(0, 1, 0);

      const delta = new THREE.Vector3();
      if (keys['w']) delta.addScaledVector(dir,   MOVE_SPEED);
      if (keys['s']) delta.addScaledVector(dir,  -MOVE_SPEED);
      if (keys['a']) delta.addScaledVector(right, -MOVE_SPEED);
      if (keys['d']) delta.addScaledVector(right,  MOVE_SPEED);
      if (keys['q']) delta.addScaledVector(up,    -MOVE_SPEED);
      if (keys['e']) delta.addScaledVector(up,     MOVE_SPEED);

      cam.position.add(delta);

      // Also move the orbit controls target so rotation stays centred
      const controls = Graph.controls();
      if (controls && controls.target) {
        controls.target.add(delta);
        controls.update();
      }
    }

    animateWASD();

    // ════════════════════════════════════════════════════════════════════════════
    // CHAT
    // ════════════════════════════════════════════════════════════════════════════
    let history     = [];
    let isStreaming = false;

    const messagesEl = document.getElementById('messages');
    function scrollBottom() { messagesEl.scrollTop = messagesEl.scrollHeight; }

    function esc(s) {
      return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')
                      .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    function addUserBubble(text) {
      const row = document.createElement('div'); row.className = 'row-user';
      const b   = document.createElement('div'); b.className = 'bubble-user';
      b.textContent = text; row.appendChild(b); messagesEl.appendChild(row);
      scrollBottom();
    }

    function createAssistantBubble() {
      const row    = document.createElement('div'); row.className = 'row-assistant';
      const bubble = document.createElement('div'); bubble.className = 'bubble-assistant';
      row.appendChild(bubble); messagesEl.appendChild(row); scrollBottom();

      const thinking = document.createElement('span');
      thinking.className = 'thinking'; thinking.textContent = 'Thinking...';
      bubble.appendChild(thinking);

      let thinkingGone  = false;
      let currentTextEl = null;
      let currentText   = '';
      const allTextEls  = [];

      function removeThinking() {
        if (!thinkingGone) { thinking.remove(); thinkingGone = true; }
      }
      function ensureTextEl() {
        if (!currentTextEl) {
          removeThinking();
          currentTextEl = document.createElement('div');
          currentTextEl.className = 'prose';
          bubble.appendChild(currentTextEl);
          allTextEls.push(currentTextEl);
        }
      }

      return {
        addText(delta) {
          ensureTextEl();
          currentText += delta;
          currentTextEl.innerHTML = marked.parse(currentText);
          scrollBottom();
        },
        addTool(name, args, summary) {
          removeThinking();
          currentTextEl = null; currentText = '';
          const d = document.createElement('details');
          d.className = 'tool-block';
          d.innerHTML = `<summary>${esc(name)} — <code>${esc(args)}</code></summary>`
                      + `<div class="tool-result">${esc(summary)}</div>`;
          bubble.appendChild(d); scrollBottom();
        },
        finalize(verses) {
          allTextEls.forEach(el => wrapVerseRefs(el, verses));
          scrollBottom();
        },
        setError(msg) {
          removeThinking();
          const e = document.createElement('div');
          e.style.cssText = 'color:#f87171;font-size:0.82em;margin-top:4px';
          e.textContent = 'Error: ' + msg; bubble.appendChild(e);
        },
      };
    }

    // ── verse tooltip ────────────────────────────────────────────────────────────
    const VREF_SPLIT = /(\[\d+:\d+\])/;
    const VREF_MATCH = /^\[(\d+:\d+)\]$/;

    function wrapVerseRefs(container, verses) {
      const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
      const targets = [];
      let node;
      while ((node = walker.nextNode())) {
        if (/\[\d+:\d+\]/.test(node.textContent)) targets.push(node);
      }
      targets.forEach(tn => {
        const parts = tn.textContent.split(VREF_SPLIT);
        if (parts.length <= 1) return;
        const frag = document.createDocumentFragment();
        parts.forEach(part => {
          const m = part.match(VREF_MATCH);
          if (m) {
            const span = document.createElement('span');
            span.className = 'vref'; span.textContent = part;
            span.dataset.vid = m[1]; span.dataset.v = verses[m[1]] || '';
            frag.appendChild(span);
          } else if (part) {
            frag.appendChild(document.createTextNode(part));
          }
        });
        tn.parentNode.replaceChild(frag, tn);
      });
    }

    const tooltip     = document.getElementById('tooltip');
    const tooltipRef  = document.getElementById('tooltip-ref');
    const tooltipText = document.getElementById('tooltip-text');

    document.addEventListener('mouseover', e => {
      const el = e.target.closest('.vref');
      if (!el || !el.dataset.v) return;
      tooltipRef.textContent  = el.dataset.vid;
      tooltipText.textContent = el.dataset.v;
      tooltip.style.display   = 'block';
      tooltip.style.visibility = 'hidden';
      const r  = el.getBoundingClientRect();
      const tw = Math.min(340, window.innerWidth - 16);
      tooltip.style.maxWidth = tw + 'px';
      const th = tooltip.offsetHeight;
      tooltip.style.visibility = '';
      let left = r.left + r.width / 2 - tw / 2;
      left = Math.max(8, Math.min(left, window.innerWidth - tw - 8));
      tooltip.style.left = left + 'px';
      tooltip.style.top  = (r.top - th - 8 < 8 ? r.bottom + 8 : r.top - th - 8) + 'px';
    });
    document.addEventListener('mouseout', e => {
      if (e.target.closest('.vref')) tooltip.style.display = 'none';
    });

    // ── send ─────────────────────────────────────────────────────────────────────
    async function sendMessage() {
      const inputEl = document.getElementById('input');
      const message = inputEl.value.trim();
      if (!message || isStreaming) return;

      inputEl.value = ''; isStreaming = true;
      document.getElementById('send-btn').disabled = true;
      examplesEl.style.display = 'none';

      addUserBubble(message);
      history.push({ role: 'user', content: message });

      const { addText, addTool, finalize, setError } = createAssistantBubble();
      let fullText = '';

      try {
        const resp = await fetch('/chat', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message, history: history.slice(0, -1) }),
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        const reader = resp.body.getReader();
        const dec    = new TextDecoder();
        let   buf    = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += dec.decode(value, { stream: true });
          const lines = buf.split('\n'); buf = lines.pop();

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            let ev;
            try { ev = JSON.parse(line.slice(6)); } catch { continue; }

            if (ev.t === 'text') {
              fullText += ev.d; addText(ev.d);
            } else if (ev.t === 'tool') {
              addTool(ev.name, ev.args, ev.summary);
            } else if (ev.t === 'graph_update') {
              applyGraphUpdate(ev);
            } else if (ev.t === 'done') {
              finalize(ev.verses || {});
              history.push({ role: 'assistant', content: fullText });
            } else if (ev.t === 'error') {
              setError(ev.d);
            }
          }
        }
      } catch (err) {
        setError(err.message);
      }

      isStreaming = false;
      document.getElementById('send-btn').disabled = false;
      inputEl.focus();
    }

    document.getElementById('input').addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
  