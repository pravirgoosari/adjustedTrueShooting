<script lang="ts">
  import { onMount, tick } from "svelte";

  type Option = { value: string; label: string };
  let {
    id,
    label,
    options,
    value = $bindable(""),
    disabled = false,
    compact = false,
    align = "left",
    onchange,
  }: {
    id: string;
    label: string;
    options: Option[];
    value?: string;
    disabled?: boolean;
    compact?: boolean;
    align?: "left" | "right";
    onchange?: () => void;
  } = $props();

  let open = $state(false);
  let active = $state(0);
  let trigger = $state<HTMLButtonElement>();
  let menu = $state<HTMLDivElement>();
  let left = $state(0);
  let top = $state(0);
  let width = $state(160);
  let maxHeight = $state(260);
  let typed = "";
  let typedAt = 0;
  const selectedLabel = $derived(
    options.find((option) => option.value === value)?.label ?? "—",
  );
  const listId = $derived(id + "-options");

  // Rendering at document level avoids clipping by the table's rounded container.
  function portal(node: HTMLDivElement) {
    document.body.appendChild(node);
    return {
      destroy() {
        node.remove();
      },
    };
  }

  function positionMenu() {
    if (!open || !trigger) return;
    const rect = trigger.getBoundingClientRect();
    if (rect.bottom < 0 || rect.top > window.innerHeight) {
      open = false;
      return;
    }
    width = Math.min(Math.max(rect.width, 160), window.innerWidth - 24);
    left = Math.max(
      12,
      Math.min(
        align === "right" ? rect.right - width : rect.left,
        window.innerWidth - width - 12,
      ),
    );
    const below = window.innerHeight - rect.bottom - 20;
    const above = rect.top - 20;
    const desired = Math.min(260, options.length * 36 + 12);
    const upwards = below < desired && above > below;
    maxHeight = Math.max(48, Math.min(260, upwards ? above : below));
    top = upwards
      ? Math.max(12, rect.top - Math.min(desired, maxHeight) - 8)
      : rect.bottom + 8;
  }
  async function revealActive() {
    await tick();
    menu
      ?.querySelector<HTMLElement>('[data-highlighted="true"]')
      ?.scrollIntoView({ block: "nearest" });
  }
  function show() {
    if (disabled || !options.length) return;
    active = Math.max(
      0,
      options.findIndex((option) => option.value === value),
    );
    open = true;
    positionMenu();
    void revealActive();
  }
  function choose(index: number, focus = true) {
    const option = options[index];
    if (!option) return;
    value = option.value;
    open = false;
    onchange?.();
    if (focus) trigger?.focus({ preventScroll: true });
  }
  function keydown(event: KeyboardEvent) {
    if (disabled || !options.length || event.ctrlKey || event.metaKey) return;
    const key = event.key;
    if (key === "Escape") {
      if (open) event.preventDefault();
      open = false;
      return;
    }
    if (key === "Tab") {
      if (open) choose(active, false);
      return;
    }
    if (key === "ArrowUp" && event.altKey && open) {
      event.preventDefault();
      choose(active);
      return;
    }
    if (key === "Enter" || key === " ") {
      event.preventDefault();
      if (open) choose(active);
      else show();
      return;
    }
    if (
      ["ArrowDown", "ArrowUp", "Home", "End", "PageDown", "PageUp"].includes(
        key,
      )
    ) {
      event.preventDefault();
      const wasOpen = open;
      if (!open) show();
      if (key === "Home") active = 0;
      else if (key === "End") active = options.length - 1;
      else if (wasOpen) {
        const step =
          key === "PageDown"
            ? 10
            : key === "PageUp"
              ? -10
              : key === "ArrowDown"
                ? 1
                : -1;
        active = Math.max(0, Math.min(options.length - 1, active + step));
      }
      void revealActive();
    } else if (key.length === 1 && !event.altKey) {
      event.preventDefault();
      if (!open) show();
      const now = Date.now();
      typed = now - typedAt > 700 ? key : typed + key;
      typedAt = now;
      const query = [...typed].every((char) => char === typed[0])
        ? typed[0]
        : typed;
      for (let offset = 1; offset <= options.length; offset++) {
        const index = (active + offset) % options.length;
        if (
          options[index].label.toLowerCase().startsWith(query.toLowerCase())
        ) {
          active = index;
          void revealActive();
          break;
        }
      }
    }
  }
  onMount(() => {
    function outside(event: Event) {
      if (
        open &&
        event.target instanceof Node &&
        !trigger?.contains(event.target) &&
        !menu?.contains(event.target)
      )
        open = false;
    }
    function scroll(event: Event) {
      if (!(event.target instanceof Node) || !menu?.contains(event.target))
        positionMenu();
    }
    document.addEventListener("pointerdown", outside);
    document.addEventListener("focusin", outside);
    window.addEventListener("resize", positionMenu);
    window.addEventListener("scroll", scroll, true);
    return () => {
      document.removeEventListener("pointerdown", outside);
      document.removeEventListener("focusin", outside);
      window.removeEventListener("resize", positionMenu);
      window.removeEventListener("scroll", scroll, true);
    };
  });
  $effect(() => {
    if (disabled) open = false;
  });
</script>

<button
  {id}
  type="button"
  class="dropdown-trigger"
  class:compact
  class:expanded={open}
  bind:this={trigger}
  {disabled}
  role="combobox"
  aria-label={label}
  aria-expanded={open}
  aria-haspopup="listbox"
  aria-controls={open ? listId : undefined}
  aria-activedescendant={open ? id + "-option-" + active : undefined}
  onkeydown={keydown}
  onclick={() => {
    if (open) open = false;
    else show();
  }}
>
  <span>{selectedLabel}</span>
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.6"
    aria-hidden="true"><path d="m7 10 5 5 5-5" /></svg
  >
</button>

{#if open}
  <div
    use:portal
    bind:this={menu}
    id={listId}
    class="dropdown-menu"
    role="listbox"
    aria-label={label}
    style:left={left + "px"}
    style:top={top + "px"}
    style:width={width + "px"}
    style:max-height={maxHeight + "px"}
  >
    {#each options as option, index (option.value)}
      <button
        type="button"
        id={id + "-option-" + index}
        role="option"
        tabindex="-1"
        aria-selected={option.value === value}
        data-highlighted={active === index}
        class="dropdown-option"
        class:selected={option.value === value}
        onpointermove={() => (active = index)}
        onpointerdown={(event) => {
          if (event.pointerType === "mouse") event.preventDefault();
        }}
        onclick={() => choose(index)}
      >
        <span>{option.label}</span>
        {#if option.value === value}
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            aria-hidden="true"><path d="m5 12 4 4L19 6" /></svg
          >
        {/if}
      </button>
    {/each}
  </div>
{/if}

<style>
  .dropdown-trigger {
    display: inline-flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    min-width: 127px;
    min-height: 40px;
    padding: 10px 12px;
    border: 1px solid var(--line);
    border-radius: 6px;
    background: #fdfdfa;
    color: var(--ink);
    font-size: 12px;
    font-weight: 550;
    white-space: nowrap;
    transition:
      border-color 0.15s,
      box-shadow 0.15s,
      background 0.15s;
  }
  .dropdown-trigger svg {
    color: #818a72;
    transition: transform 0.15s;
  }
  .dropdown-trigger:hover:not(:disabled) {
    border-color: #c9cebd;
    background: #f7f8f0;
  }
  .dropdown-trigger.expanded {
    border-color: #d6a68b;
    box-shadow: 0 0 0 3px #d35b3010;
  }
  .dropdown-trigger.expanded svg {
    transform: rotate(180deg);
    color: var(--accent);
  }
  .dropdown-trigger:focus-visible {
    outline: 2px solid #d6a68b;
    outline-offset: 2px;
  }
  .dropdown-trigger:disabled {
    opacity: 0.6;
  }
  .dropdown-trigger.compact {
    min-width: 112px;
    min-height: 37px;
    padding: 8px 12px;
    font-size: 11px;
    font-weight: 450;
  }
  .dropdown-menu {
    position: fixed;
    z-index: 100;
    overflow-y: auto;
    overscroll-behavior: contain;
    padding: 5px;
    border: 1px solid #dfe3d3;
    border-radius: 9px;
    background: #fdfdf8;
    box-shadow:
      0 12px 32px #303b2117,
      0 2px 6px #303b2108;
    scrollbar-width: thin;
    scrollbar-color: #cfd5c1 transparent;
  }
  .dropdown-option {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    width: 100%;
    height: 36px;
    padding: 0 10px;
    border-radius: 5px;
    text-align: left;
    font-size: 12px;
    color: #626b54;
    background: transparent;
  }
  .dropdown-option[data-highlighted="true"] {
    background: #edf0e4;
    color: #35402a;
  }
  .dropdown-option.selected {
    background: #faeee3;
    color: #b7532b;
    font-weight: 600;
  }
  .dropdown-option.selected[data-highlighted="true"] {
    background: #f6e5d7;
  }
  @media (max-width: 640px) {
    .dropdown-trigger {
      min-width: 112px;
      min-height: 34px;
      padding: 7px 12px;
      font-size: 11px;
    }
    .dropdown-trigger.compact {
      min-width: 100px;
      font-size: 12px;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .dropdown-trigger,
    .dropdown-trigger svg {
      transition: none;
    }
  }
</style>
