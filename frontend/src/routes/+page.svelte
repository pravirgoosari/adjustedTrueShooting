<script lang="ts">
  import { onMount } from 'svelte';

  type PlayerRow = {
    Player: string;
    Team: string;
    Season: string;
    PPG: number;
    'aTS%': number;
    'TS%': number;
    DIFF: number;
    'Usage Rate': number;
    'Team 3PT%': number;
    'Team 3PA': number;
  };

  type SeasonResponse = {
    season_data: Record<string, PlayerRow[]>;
    seasons: number[];
    default_season: number;
    generated_at: string;
  };

  const columns: Array<{ label: string; key: keyof PlayerRow; numeric: boolean }> = [
    { label: 'Player', key: 'Player', numeric: false },
    { label: 'Team', key: 'Team', numeric: false },
    { label: 'Season', key: 'Season', numeric: false },
    { label: 'PPG', key: 'PPG', numeric: true },
    { label: 'aTS%', key: 'aTS%', numeric: true },
    { label: 'TS%', key: 'TS%', numeric: true },
    { label: 'DIFF', key: 'DIFF', numeric: true },
    { label: 'Usage Rate', key: 'Usage Rate', numeric: true },
    { label: 'Team 3PT%', key: 'Team 3PT%', numeric: true },
    { label: 'Team 3PA', key: 'Team 3PA', numeric: true }
  ];

  let activePage = $state('dataPage');
  let seasons = $state<number[]>([]);
  let selectedSeason = $state('');
  let seasonData = $state<Record<string, PlayerRow[]>>({});
  let sortColumn = $state<number | null>(null);
  let sortDirection = $state<'asc' | 'desc'>('asc');
  let sortedSeason = $state('');

  let visibleRows = $derived.by(() => {
    const rows = [...(seasonData[selectedSeason] ?? [])];
    if (sortColumn === null || sortedSeason !== selectedSeason) return rows;

    const column = columns[sortColumn];
    return rows.sort((a, b) => {
      const aValue = a[column.key];
      const bValue = b[column.key];
      const comparison = column.numeric
        ? (Number(aValue) || 0) - (Number(bValue) || 0)
        : String(aValue).localeCompare(String(bValue));
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  });

  onMount(async () => {
    const response = await fetch('/api/data');
    if (!response.ok) throw new Error('Unable to load season data');
    const data: SeasonResponse = await response.json();
    seasons = data.seasons;
    selectedSeason = String(data.default_season);
    seasonData = data.season_data;
  });

  function showPage(pageId: string) {
    activePage = pageId;
  }

  function selectPage(event: MouseEvent, pageId: string) {
    event.preventDefault();
    showPage(pageId);
  }

  function showSeasonData(season: string) {
    selectedSeason = season;
  }

  function sortTable(columnIndex: number) {
    if (sortColumn === columnIndex && sortDirection === 'asc') {
      sortDirection = 'desc';
    } else {
      sortColumn = columnIndex;
      sortDirection = 'asc';
    }
    sortedSeason = selectedSeason;
  }

  function formatNumber(value: number) {
    return Number(value).toFixed(1);
  }
</script>

<svelte:head>
  <title>Adjusted True Shooting</title>
</svelte:head>

<div class="container mt-5">
  <div class="navbar">
    <div class="nav-left">
      <ul>
        <li><a href="/" class="active" onclick={(event) => selectPage(event, 'dataPage')}>aTS% DATA</a></li>
        <li><a href="/" onclick={(event) => selectPage(event, 'aboutATSPage')}>ABOUT aTS%</a></li>
        <li><a href="/" onclick={(event) => selectPage(event, 'aboutDevelopmentPage')}>ABOUT DEVELOPMENT</a></li>
        <li><a href="/" onclick={(event) => selectPage(event, 'aboutMePage')}>ABOUT ME</a></li>
      </ul>
    </div>
    <div class="nav-right">
      <a href="https://www.linkedin.com/in/pravirgoosari/" target="_blank" class="linkedin-button">LINKEDIN</a>
      <a href="https://github.com/pravirgoosari" target="_blank" class="github-button">GITHUB</a>
    </div>
  </div>

  {#if activePage === 'dataPage'}
    <div id="dataPage" class="page-content">
      <div class="page-title"><h1>ADJUSTED TRUE SHOOTING</h1></div>
      <div class="season-selector">
        <span class="season-label">SEASON:</span>
        <select id="seasonSelect" bind:value={selectedSeason} onchange={(event) => showSeasonData(event.currentTarget.value)}>
          {#each seasons as season}
            <option value={String(season)}>{season}</option>
          {/each}
        </select>
      </div>
      <div class="table-container">
        <div class="table-scroll">
          <table id="playerDataTable" class="table table-striped">
            <thead>
              <tr>
                {#each columns as column, index}
                  <th data-dir={sortColumn === index ? sortDirection : undefined} onclick={() => sortTable(index)}>{column.label}</th>
                {/each}
              </tr>
            </thead>
            <tbody id="playerTableBody">
              {#each visibleRows as row, index}
                <tr class="season-data" data-season={selectedSeason} style:background-color={index % 2 === 0 ? '#fff' : '#f8f9fa'}>
                  <td>{row.Player}</td><td>{row.Team}</td><td>{row.Season}</td><td>{formatNumber(row.PPG)}</td>
                  <td>{formatNumber(row['aTS%'])}</td><td>{formatNumber(row['TS%'])}</td><td>{formatNumber(row.DIFF)}</td><td>{formatNumber(row['Usage Rate'])}</td>
                  <td>{formatNumber(row['Team 3PT%'])}</td><td>{formatNumber(row['Team 3PA'])}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  {:else if activePage === 'aboutATSPage'}
    <div id="aboutATSPage" class="info-content">
      <h1>ABOUT aTS%</h1>
      <div class="info-text">
        <p>Adjusted True Shooting (aTS%) is an advanced version of the commonly used True Shooting % (TS%). While TS% offers a solid measure of efficiency, it doesn't account for key factors that impact a player's shooting performance—notably usage rate and team spacing. Higher usage draws more defensive attention and makes shot attempts more difficult, while better team spacing can make shots easier to obtain.</p>
        <ul class="feature-list">
          <li><strong>Usage Rate:</strong> Measures how many possessions a player uses, indicating defensive attention</li>
          <li><strong>Team Spacing:</strong> Composite score combining team's three-point volume and efficiency</li>
          <li><strong>Machine Learning:</strong> Uses Random Forest regression to learn complex relationships</li>
        </ul>
        <p>The model predicts an expected TS% based on a player's usage rate and their team's spacing quality. Players who exceed these expectations receive positive adjustments to their aTS%, while those who fall short are penalized. This creates a more nuanced efficiency metric that accounts for both individual role and team context. The model shows that usage rate accounts for roughly 63% of the adjustment, while team spacing contributes about 37%, validating the significant impact of both factors on shooting efficiency.</p>
      </div>
    </div>
  {:else if activePage === 'aboutDevelopmentPage'}
    <div id="aboutDevelopmentPage" class="info-content">
      <h1>ABOUT DEVELOPMENT</h1>
      <div class="info-text">
        <p>This project combines modern web development with advanced machine learning to create an interactive platform for basketball analytics. The backend is built using Python and Flask, with data processing handled by pandas and numpy. The statistical engine employs scikit-learn's Random Forest Regressor, which can capture complex non-linear relationships between player usage, team spacing, and shooting efficiency.</p>
        <p>Key technical features include:</p>
        <ul class="feature-list">
          <li>Random Forest model that learns from historical NBA data</li>
          <li>Composite spacing score using geometric mean of 3PT% and 3PA</li>
          <li>Feature scaling to ensure fair comparison across metrics</li>
          <li>Automated data pipeline for multiple NBA seasons</li>
        </ul>
        <p>The frontend provides an intuitive interface to explore these advanced analytics, with dynamic sorting and filtering capabilities. All calculations are performed server-side for consistency and reliability.</p>
      </div>
    </div>
  {:else if activePage === 'aboutMePage'}
    <div id="aboutMePage" class="info-content">
      <h1>ABOUT ME</h1>
      <div class="info-text">
        <p>I am a graduate from the University of Washington with a B.S. in Electrical and Computer Engineering (Class of 2026), where my academic focus intersected perfectly with my passion for basketball analytics. This unique combination of engineering and sports has driven me to develop innovative ways to understand the game through data.</p>
        <p>My journey in basketball analytics has led me to create 'aTS%' (Adjusted True Shooting Percentage), a statistic that redefines how we measure player efficiency by considering usage rate and team spacing. This project represents the perfect blend of my technical skills and basketball knowledge, utilizing machine learning to provide deeper insights into player performance.</p>
        <p>Beyond the technical aspects, I share my basketball insights through 'HoopsLine,' an Instagram page where I combine analytics with creative design to engage with the basketball community. Through this platform, I aim to bridge the gap between traditional basketball knowledge and modern analytical approaches, fostering discussions about the evolving nature of the game.</p>
      </div>
    </div>
  {/if}
</div>
