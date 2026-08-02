<script lang="ts">
  import { onMount } from "svelte";
  import Dropdown from "$lib/Dropdown.svelte";
  import { teamColors } from "$lib/teamColors";
  type PlayerRow = {
    Position?: string;
    Player: string;
    Team: string;
    Season: string;
    PPG: number;
    MPG: number;
    GP: number;
    "aTS%": number;
    "TS%": number;
    DIFF: number;
    "Usage Rate": number;
    "Team 3PT%": number;
    "Team 3PA": number;
  };
  type SeasonResponse = {
    season_data: Record<string, PlayerRow[]>;
    playoff_data: Record<string, PlayerRow[]>;
    seasons: number[];
    default_season: number;
    default_season_type: string;
    generated_at: string;
  };
  const pages = [
    { id: "data", label: "aTS%" },
    { id: "method", label: "About aTS%" },
    { id: "development", label: "About Development" },
    { id: "about", label: "About Me" },
  ];
  const columns: {
    label: string;
    key: keyof PlayerRow;
    numeric: boolean;
    description: string;
  }[] = [
    {
      label: "Player",
      key: "Player",
      numeric: false,
      description: "Player name",
    },
    { label: "Team", key: "Team", numeric: false, description: "NBA team" },
    {
      label: "GP",
      key: "GP",
      numeric: true,
      description: "Games played",
    },
    { label: "MPG", key: "MPG", numeric: true, description: "Minutes per game" },
    { label: "PPG", key: "PPG", numeric: true, description: "Points per game" },
    {
      label: "aTS%",
      key: "aTS%",
      numeric: true,
      description: "adjusted True Shooting Percentage",
    },
    {
      label: "TS%",
      key: "TS%",
      numeric: true,
      description: "True Shooting Percentage",
    },
    {
      label: "Diff",
      key: "DIFF",
      numeric: true,
      description: "aTS% minus TS%, in percentage points",
    },
    {
      label: "Usage",
      key: "Usage Rate",
      numeric: true,
      description: "Usage rate",
    },
    {
      label: "Team 3PT%",
      key: "Team 3PT%",
      numeric: true,
      description: "Team three-point percentage",
    },
    {
      label: "Team 3PA",
      key: "Team 3PA",
      numeric: true,
      description: "Team three-point attempts per game",
    },
  ];
  let activePage = $state("data");
  let seasons = $state<number[]>([]);
  let selectedSeason = $state("2026");
  let selectedType = $state("regular");
  const seasonTypes = [
    { value: "regular", label: "Regular Season" },
    { value: "playoffs", label: "Playoffs" },
  ];
  const selectedTypeLabel = $derived(selectedType === "playoffs" ? "Playoffs" : "Regular Season");
  let seasonData = $state<Record<string, PlayerRow[]>>({});
  let playoffData = $state<Record<string, PlayerRow[]>>({});
  let generatedAt = $state("");
  let loading = $state(true);
  let error = $state("");
  let search = $state("");
  let team = $state("all");
  type StatFilter = {
    id: number;
    key: string;
    min: number | undefined;
    max: number | undefined;
  };
  const filterColumns = columns.filter((column) => column.numeric);
  let filtersOpen = $state(false);
  let statFilters = $state<StatFilter[]>([]);
  let nextFilterId = 0;
  const activeFilterCount = $derived(
    statFilters.filter((filter) => filter.min !== undefined || filter.max !== undefined).length,
  );
  function resetTableScroll() {
    if (tableScroll) tableScroll.scrollTop = 0;
  }
  function addStatFilter() {
    const column = filterColumns.find((column) => !statFilters.some((filter) => filter.key === column.key));
    if (column) statFilters.push({ id: nextFilterId++, key: column.key, min: undefined, max: undefined });
  }
  function removeStatFilter(id: number) {
    statFilters = statFilters.filter((filter) => filter.id !== id);
    resetTableScroll();
  }
  let sortColumn = $state(columns.findIndex((column) => column.key === "PPG"));
  let sortDirection = $state<"asc" | "desc">("desc");
  let tableScroll = $state<HTMLDivElement>();
  const seasonRows = $derived(
    (selectedType === "playoffs" ? playoffData : seasonData)[selectedSeason] ?? [],
  );
  const teams = $derived(
    [...new Set(seasonRows.map((row) => row.Team))].sort(),
  );
  const normalize = (value: string) =>
    value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  const visibleRows = $derived.by(() => {
    const query = normalize(search.trim());
    const rows = seasonRows.filter(
      (row) =>
        (team === "all" || row.Team === team) &&
        normalize(row.Player).includes(query) &&
        statFilters.every((filter) => {
          const value = Number(row[filter.key as keyof PlayerRow]);
          return (filter.min === undefined || value >= filter.min) &&
            (filter.max === undefined || value <= filter.max);
        }),
    );
    const column = columns[sortColumn];
    return rows.sort((a, b) => {
      const comparison = column.numeric
        ? Number(a[column.key]) - Number(b[column.key])
        : String(a[column.key]).localeCompare(String(b[column.key]));
      return sortDirection === "asc" ? comparison : -comparison;
    });
  });
  const topScorer = $derived([...seasonRows].sort((a, b) => b.PPG - a.PPG)[0]);
  const efficiencyLeader = $derived(
    [...seasonRows]
      .filter((row) => row.PPG >= 20 && (selectedType === "playoffs" || row.GP >= 5))
      .sort((a, b) => b["aTS%"] - a["aTS%"])[0],
  );
  const updatedLabel = $derived(
    generatedAt
      ? new Intl.DateTimeFormat("en-US", {
          month: "short",
          day: "numeric",
          year: "numeric",
          timeZone: "UTC",
        }).format(new Date(generatedAt))
      : "",
  );
  async function loadData() {
    loading = true;
    error = "";
    try {
      const response = await fetch("/api/data");
      if (!response.ok) throw new Error("Unable to load season data");
      const data: SeasonResponse = await response.json();
      seasons = data.seasons;
      selectedSeason = String(data.default_season);
      seasonData = data.season_data;
      playoffData = data.playoff_data;
      selectedType = data.default_season_type;
      generatedAt = data.generated_at;
    } catch {
      error = "The season data couldn’t be loaded. Please try again.";
    } finally {
      loading = false;
    }
  }
  onMount(() => {
    void loadData();
  });
  function changeSeason() {
    team = "all";
    if (tableScroll) tableScroll.scrollTop = 0;
  }
  function sortTable(index: number) {
    sortDirection =
      sortColumn === index
        ? sortDirection === "asc"
          ? "desc"
          : "asc"
        : columns[index].numeric
          ? "desc"
          : "asc";
    sortColumn = index;
    if (tableScroll) tableScroll.scrollTop = 0;
  }
  const formatNumber = (value: number) => Number(value).toFixed(1);
  const seasonLabel = (value: string | number) =>
    String(Number(value) - 1) + "–" + String(value).slice(-2);
</script>

<svelte:head>
  <title
    >{activePage === "data"
      ? "Player Explorer"
      : pages.find((page) => page.id === activePage)?.label} · aTS%</title
  >
  <meta
    name="description"
    content="Explore NBA shooting efficiency with Adjusted True Shooting. The numbers, with usage and team spacing taken into account."
  />
</svelte:head>

{#snippet arrow()}
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.7"
    aria-hidden="true"><path d="M7 17 17 7M7 7h10v10" /></svg
  >
{/snippet}

{#snippet sortArrow(direction: "asc" | "desc" | "both" = "both")}
  <svg width="12" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
    <path d="M12 4v16" />
    {#if direction !== "desc"}<path d="m7 9 5-5 5 5" />{/if}
    {#if direction !== "asc"}<path d="m7 15 5 5 5-5" />{/if}
  </svg>
{/snippet}

<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="header-inner">
    <button
      class="brand"
      onclick={() => (activePage = "data")}
      aria-label="aTS% home"
    >
      <img class="brand-logo" src="/favicon.ico" alt="" width="80" height="80" />
      <span
        ><span class="brand-divider"
        ></span><span class="brand-caption">adjusted True Shooting %</span></span
      >
    </button>
    <nav aria-label="Main navigation">
      {#each pages as page}
        <button
          class:active={activePage === page.id}
          aria-current={activePage === page.id ? "page" : undefined}
          onclick={() => (activePage = page.id)}>{page.label}</button
        >
      {/each}
    </nav>
    <a
      class="source-link"
      href="https://github.com/pravirgoosari/adjustedTrueShooting"
      target="_blank"
      rel="noreferrer">View Project {@render arrow()}</a
    >
  </div>
</header>

<main id="main" class="main-shell">
  {#if activePage === "data"}
    <section class="hero" aria-labelledby="hero-title">
      <div class="hero-copy">
        <div class="eyebrow">
          <span class="orange-dot"></span> NBA Analytics
        </div>
        <h1 id="hero-title">adjusted True Shooting <span>%</span></h1>
        <p>
          This stat looks at how much a player's usage and team spacing impacts their efficiency.<br
            class="desktop-break"
          /> Explore adjusted True Shooting % below.
        </p>
        <button class="text-link" onclick={() => (activePage = "method")}
          >Get to know aTS% {@render arrow()}</button
        >
      </div>
    </section>
    <section class="snapshot" aria-label="Season overview">
      <div class="snapshot-context">
        <span class="eyebrow">The season at a glance</span><strong
          >{seasonLabel(selectedSeason)} <span>{selectedTypeLabel}</span></strong
        >
      </div>
      <div class="snapshot-stat">
        <span class="stat-label">Players in the Dataset</span>
        <div>
          <strong>{loading ? "—" : seasonRows.length}</strong><span
            >Across the League</span
          >
        </div>
      </div>
      <div class="snapshot-stat">
        <span class="stat-label">Leading Scorer</span>
        <div>
          <strong
            >{topScorer ? formatNumber(topScorer.PPG) : "—"}<small>
              PPG</small
            ></strong
          ><span>{topScorer?.Player ?? "—"}</span>
        </div>
      </div>
      <div class="snapshot-stat">
        <span class="stat-label"
          >aTS% Leader <span class="qualifier">20+ PPG</span></span
        >
        <div>
          <strong class="accent-text"
            >{efficiencyLeader
              ? formatNumber(efficiencyLeader["aTS%"])
              : "—"}<small>%</small></strong
          ><span>{efficiencyLeader?.Player ?? "—"}</span>
        </div>
      </div>
    </section>
    <section class="explorer" aria-labelledby="explorer-title">
      <div class="explorer-heading">
        <div>
          <div class="section-kicker">The numbers</div>
          <h2 id="explorer-title">
            Player Explorer<span class="count-badge">{seasonRows.length}</span>
          </h2>
        </div>
        <div class="dataset-controls">
          <div class="season-control">
          <label for="seasonSelect">Season</label><Dropdown
            id="seasonSelect"
            label="Season"
            bind:value={selectedSeason}
            onchange={changeSeason}
            disabled={loading}
            align="right"
            options={seasons.map(season => ({ value: String(season), label: seasonLabel(season) }))}
          />
          </div>
          <div class="season-control type-control">
            <label for="typeSelect">Type</label><Dropdown
              id="typeSelect"
              label="Type"
              bind:value={selectedType}
              onchange={changeSeason}
              disabled={loading}
              align="right"
              options={seasonTypes}
            />
          </div>
        </div>
      </div>
      <p class="mobile-scroll-hint">Swipe the table for more stats <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true" focusable="false"><path d="M4 12h16m-6-6 6 6-6 6" /></svg></p>
      <div class="data-panel">
        <div class="table-toolbar">
          <label class="search-box"
            ><svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.7"
              aria-hidden="true"
              ><circle cx="10.5" cy="10.5" r="6.5" /><path
                d="m16 16 4.5 4.5"
              /></svg
            ><input
              type="search"
              aria-label="Search players"
              placeholder="Find a Player"
              bind:value={search}
              oninput={() => {
                if (tableScroll) tableScroll.scrollTop = 0;
              }}
            /></label
          >
          <Dropdown
            id="teamSelect"
            label="Filter by team"
            compact
            bind:value={team}
            onchange={() => {
              if (tableScroll) tableScroll.scrollTop = 0;
            }}
            options={[{ value: 'all', label: 'All Teams' }, ...teams.map(name => ({ value: name, label: name }))]}
          />
          <button
            class="stat-filter-toggle"
            class:has-filters={activeFilterCount > 0}
            aria-expanded={filtersOpen}
            aria-controls="stat-filters"
            onclick={() => {
              filtersOpen = !filtersOpen;
              if (filtersOpen && !statFilters.length) addStatFilter();
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M4 7h16M4 17h16" /><circle cx="9" cy="7" r="3" fill="var(--paper)" /><circle cx="15" cy="17" r="3" fill="var(--paper)" /></svg>
            Filters{#if activeFilterCount}<span class="filter-count">{activeFilterCount}</span>{/if}
          </button>
          <span class="toolbar-note"
            ><span class="legend-dot"></span> Adjusted for Context</span
          >
        </div>
        <section id="stat-filters" class="stat-filters" aria-label="Stat filters" hidden={!filtersOpen}>
          <div class="filter-panel-heading">
            <div><strong>Filter by Stat</strong><p>Players must match all filters. Leave a limit blank for no minimum or maximum.</p></div>
            <button class="filter-text-button" onclick={() => { statFilters = []; resetTableScroll(); }}>Clear All</button>
          </div>
          {#each statFilters as filter (filter.id)}
            <div class="stat-filter-row">
              <div class="filter-column-picker">
                <label for={`filter-column-${filter.id}`}>Column</label>
                <Dropdown
                  id={`filter-column-${filter.id}`}
                  label="Filter column"
                  bind:value={filter.key}
                  onchange={resetTableScroll}
                  options={filterColumns.filter((column) => column.key === filter.key || !statFilters.some((other) => other.key === column.key)).map((column) => ({ value: column.key, label: column.label }))}
                />
              </div>
              <label class="filter-limit">
                <span>Minimum</span>
                <input type="number" step={filter.key === 'GP' ? '1' : 'any'} placeholder="No minimum" aria-label={`${filter.key} minimum`} bind:value={filter.min} oninput={resetTableScroll} />
              </label>
              <label class="filter-limit">
                <span>Maximum</span>
                <input type="number" step={filter.key === 'GP' ? '1' : 'any'} placeholder="No maximum" aria-label={`${filter.key} maximum`} bind:value={filter.max} oninput={resetTableScroll} />
              </label>
              <button class="remove-stat-filter" aria-label={`Remove ${filter.key} filter`} onclick={() => removeStatFilter(filter.id)}>×</button>
              {#if filter.min !== undefined && filter.max !== undefined && filter.min > filter.max}
                <p class="filter-range-error" role="status">Minimum must be less than or equal to maximum.</p>
              {/if}
            </div>
          {/each}
          <button class="filter-text-button" disabled={statFilters.length >= filterColumns.length} onclick={addStatFilter}>+ Add Filter</button>
        </section>
        <!-- The scroll region must be focusable for keyboard scrolling. -->
        <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
        <div
          class="table-scroll"
          bind:this={tableScroll}
          tabindex="0"
          role="region"
          aria-label="Player statistics. Scroll to see more players and columns."
          aria-busy={loading}
        >
          <table id="playerDataTable">
            <thead
              ><tr
                ><th class="rank-heading" scope="col">#</th
                >{#each columns as column, index}<th
                    scope="col"
                    class:numeric={column.numeric}
                    class:metric-column={column.key === "aTS%"}
                    aria-sort={sortColumn === index
                      ? sortDirection === "asc"
                        ? "ascending"
                        : "descending"
                      : "none"}
                    ><button
                      onclick={() => sortTable(index)}
                      title={column.description}
                      >{column.label}<span
                        class:sort-active={sortColumn === index}
                        class="sort-indicator"
                        aria-hidden="true"
                        >{@render sortArrow(sortColumn === index ? sortDirection : "both")}</span
                      ></button
                    ></th
                  >{/each}</tr
              ></thead
            >
            <tbody>
              {#if loading}<tr
                  ><td colspan={columns.length + 1} class="table-message"
                    ><span class="loading-dot"></span> Loading the season…</td
                  ></tr
                >
              {:else if error}<tr
                  ><td colspan={columns.length + 1} class="table-message"
                    ><p role="alert">{error}</p>
                    <button class="primary-button" onclick={loadData}
                      >Try again</button
                    ></td
                  ></tr
                >
              {:else if !seasonRows.length}<tr
                  ><td colspan={columns.length + 1} class="table-message"
                    >No {selectedTypeLabel.toLowerCase()} data available for {seasonLabel(selectedSeason)}.</td
                  ></tr
                >
              {:else if !visibleRows.length}<tr
                  ><td colspan={columns.length + 1} class="table-message"
                    ><strong>No players found.</strong>
                    <p>Try another name, team, or stat filter.</p>
                    <button
                      class="text-link"
                      onclick={() => {
                        search = "";
                        team = "all";
                        statFilters = [];
                      }}>Clear filters {@render arrow()}</button
                    ></td
                  ></tr
                >
              {:else}{#each visibleRows as row, index}
                  <tr class="season-data" data-season={selectedSeason} data-season-type={selectedType}>
                    <td class="rank-cell"
                      >{String(index + 1).padStart(2, "0")}</td
                    >
                    <td class="player-cell"
                      ><span class="player-avatar" title={row.Position ? 'Position: ' + row.Position : 'Position unavailable'}
                        >{row.Position ?? '—'}</span
                      ><span>{row.Player}</span></td
                    >
                    <td><span
                      class="team-badge"
                      style:background-color={teamColors[row.Team]?.main}
                      style:border-color={teamColors[row.Team]?.main}
                      style:color={teamColors[row.Team]?.secondary}
                    >{row.Team}</span></td>
                    <td class="numeric">{row.GP}</td>
                    <td class="numeric">{formatNumber(row.MPG)}</td>
                    <td class="numeric">{formatNumber(row.PPG)}</td><td
                      class="numeric metric-column"
                      >{formatNumber(row["aTS%"])}</td
                    ><td class="numeric">{formatNumber(row["TS%"])}</td>
                    <td class="numeric"
                      ><span
                        class="diff-value"
                        class:positive={row.DIFF > 0}
                        class:negative={row.DIFF < 0}
                        >{row.DIFF > 0 ? "+" : ""}{formatNumber(row.DIFF)}</span
                      ></td
                    >
                    <td class="numeric">{formatNumber(row["Usage Rate"])}</td
                    ><td class="numeric">{formatNumber(row["Team 3PT%"])}</td
                    ><td class="numeric">{formatNumber(row["Team 3PA"])}</td>
                  </tr>
                {/each}{/if}
            </tbody>
          </table>
        </div>
        <div class="table-footer">
          <span aria-live="polite"
            >{visibleRows.length} of {seasonRows.length} Players<span
              class="footer-season"
            >: {seasonLabel(selectedSeason)} {selectedTypeLabel}</span
            ></span
          ><span>Click a Column to Sort <span aria-hidden="true">{@render sortArrow()}</span></span>
        </div>
      </div>
      <div class="data-note">
        <span
          ><strong>DISCLAIMER:</strong> aTS% is not perfect and should not be treated as such.</span
        ><button class="text-link" onclick={() => (activePage = "method")}
          >How it Works {@render arrow()}</button
        >
      </div>
    </section>
  {:else if activePage === "method"}
    <section class="article-hero">
      <div class="eyebrow"><span class="orange-dot"></span> The metric</div>
      <h1>Efficiency With<br /><span>Spacing and Usage</span></h1>
      <p>
        True Shooting % measures efficiency. adjusted True Shooting % adds the
        context of a player’s role and their team.
      </p>
    </section>
    <div class="article-layout">
      <aside>
        <span class="section-kicker">A closer look</span>
        <h2>Beyond the<br />Box Score</h2>
        <span class="large-metric">aTS<span>%</span></span>
      </aside>
      <article>
        <h2>Why Adjust True Shooting?</h2>
        <p>
          True Shooting % (TS%) offers a useful measure of scoring efficiency.
          But it doesn’t account for the conditions in which a player takes
          their shots. Higher usage can draw more defensive attention, while
          better team spacing can create easier opportunities.
        </p>
        <div class="method-grid">
          <div>
            <span class="step-number">01 / ROLE</span>
            <h3>Usage Rate</h3>
            <p>
              How much of the offense a player carries. A bigger role changes
              the demands placed on a scorer.
            </p>
          </div>
          <div>
            <span class="step-number">02 / SPACE</span>
            <h3>Team Spacing</h3>
            <p>
              A composite score combining a team’s three-point volume and
              efficiency.
            </p>
          </div>
        </div>
        <h2>Turning Context into a Number</h2>
        <p>
          A Random Forest regression model predicts expected TS% using player
          usage and team spacing. Players who exceed those expectations receive
          positive adjustments. Those who fall short receive negative
          adjustments.
        </p>
        <p>
          The resulting aTS% brings individual role and team context into the
          efficiency conversation. It’s another way to evaluate a player,
          alongside the rest of their game.
        </p>
        <div class="definition-box">
          <span class="section-kicker">Reading the table</span>
          <h3>The Difference Makes the Adjustment Visible.</h3>
          <p>
            <strong>Diff = aTS% − TS%.</strong> A positive number means the adjustment
            raises the player’s efficiency rating. A negative number means it lowers
            it. Differences are shown in percentage points.
          </p>
        </div>
        <button class="primary-button" onclick={() => (activePage = "data")}
          >Explore the Numbers {@render arrow()}</button
        >
      </article>
    </div>
  {:else if activePage === "development"}
    <section class="article-hero">
      <div class="eyebrow">
        <span class="orange-dot"></span> Behind the build
      </div>
      <h1>The Technology Behind<br /><span>adjusted True Shooting %</span></h1>
      <p>
        The intersection of basketball, machine learning, and
        web development.
      </p>
    </section>
    <div class="article-layout">
      <aside>
        <span class="section-kicker">The toolkit</span>
        <h2>Technical<br />Components</h2>
        <div class="stack-tags">
          <span>SvelteKit</span><span>TypeScript</span><span>Flask</span><span
            >scikit-learn</span
          ><span>pandas</span><span>NumPy</span>
        </div>
        <a
          class="text-link"
          href="https://github.com/pravirgoosari/adjustedTrueShooting"
          target="_blank"
          rel="noreferrer">Explore the Code {@render arrow()}</a
        >
      </aside>
      <article>
        <h2>Powered by Machine Learning</h2>
        <p>
          The analytics pipeline uses pandas and NumPy to process NBA season
          data. Scikit-learn’s Random Forest Regressor models the relationships
          between player usage, team spacing, and shooting efficiency.
        </p>
        <div class="build-steps">
          <div>
            <span>01</span>
            <div>
              <h3>Collect & Prepare</h3>
              <p>
                Season data is sourced through basketball-reference-web-scraper,
                processed, and organized for the model.
              </p>
            </div>
          </div>
          <div>
            <span>02</span>
            <div>
              <h3>Model & Adjust</h3>
              <p>
                Feature scaling and a geometric-mean spacing score help turn
                usage and team shooting into adjusted efficiency metrics.
              </p>
            </div>
          </div>
          <div>
            <span>03</span>
            <div>
              <h3>Serve & Explore</h3>
              <p>
                Precomputed JSON snapshots are served by Flask. SvelteKit and
                TypeScript power the interactive player table in your browser.
              </p>
            </div>
          </div>
        </div>
        <h2>Containerized Deployments</h2>
        <p>
          GitHub Actions builds the frontend, generates season snapshots, runs
          tests, and packages the application in Docker. The image is deployed
          to Azure Container Apps.
        </p>
      </article>
    </div>
  {:else}
    <section class="article-hero">
      <div class="eyebrow">
        <span class="orange-dot"></span> Learn About Me
      </div>
      <h1>My Name is<br /><span>Pravir Goosari</span></h1>
      <p>
        I built aTS% to redefine how we measure player efficiency by considering usage rate and team spacing.
      </p>
    </section>
    <div class="article-layout">
      <aside>
        <div class="profile-monogram" aria-hidden="true">PG</div>
        <h2>Pravir Goosari</h2>
        <p class="profile-subtitle">
          University of Washington<br />B.S. Electrical & Computer Engineering<br
          />Class of 2026
        </p>
        <div class="profile-links">
          <a
            class="text-link"
            href="https://www.linkedin.com/in/pravirgoosari/"
            target="_blank"
            rel="noreferrer">LinkedIn {@render arrow()}</a
          ><a
            class="text-link"
            href="https://github.com/pravirgoosari"
            target="_blank"
            rel="noreferrer">GitHub {@render arrow()}</a
          >
        </div>
      </aside>
      <article>
        <h2>Who I Am</h2>
        <p>
          I’m a University of Washington graduate with a B.S. in Electrical and
          Computer Engineering. My academic focus intersected with my passion
          for basketball analytics, inspiring me to find new ways to understand
          the game through data.
        </p>
        <p>
          aTS% grew out of that curiosity. I wanted to explore how a player’s
          offensive role and the space around them shape their shooting
          efficiency, and turn that question into something other basketball
          fans could use.
        </p>
        <h2>What I Do</h2>
        <p>
          Beyond this project, I share basketball insights through HoopsLine on
          Instagram, combining analytics with creative design. The aim is to
          connect traditional basketball knowledge with data and encourage
          conversations about the evolving game.
        </p>
        <a
          class="primary-button"
          href="https://www.instagram.com/hoopsline/"
          target="_blank"
          rel="noreferrer">@HOOPSLINE {@render arrow()}</a
        >
      </article>
    </div>
  {/if}
  <footer class="site-footer">
    <span class="footer-brand"
      >aTS%</span
    >
    <div>
      {#if updatedLabel}<span>Data Updated {updatedLabel}</span>{/if}<a
        href="https://www.linkedin.com/in/pravirgoosari/"
        target="_blank"
        rel="noreferrer">Pravir Goosari {@render arrow()}</a
      >
    </div>
  </footer>
</main>
