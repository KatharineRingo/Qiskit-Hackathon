"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { PathLayer, PolygonLayer, ScatterplotLayer, TextLayer } from "@deck.gl/layers";
import { PathStyleExtension } from "@deck.gl/extensions";
import type { Scenario, SegFeature, SegProps } from "@/lib/types";

const STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";
const BLANK: maplibregl.StyleSpecification = { version: 8, sources: {}, layers: [{ id: "bg", type: "background", paint: { "background-color": "#080a10" } }] };
const ORANGE: [number, number, number] = [255, 106, 31];
const BLUE: [number, number, number] = [75, 147, 255];
const VIOLET: [number, number, number] = [167, 139, 250];
const PAPER: [number, number, number] = [240, 239, 235];

export interface Focus { ids: string[]; nonce: number }
interface Props {
  scenario: Scenario;
  threeD: boolean;
  tideLevel: number;       // 0-1 for the selected month
  kingTide: boolean;       // selected month is in king tide season
  waterOn: boolean;
  undertowIds: string[];
  todayIds: string[];
  compare: boolean;
  selectedId: string | null;
  focus: Focus | null;
  compassNonce: number;
  onSelect: (p: SegProps | null) => void;
  onBearing: (b: number) => void;
}

const reduce = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const PITCH = 45;

export default function MapView(p: Props) {
  const box = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const overlayRef = useRef<MapboxOverlay | null>(null);
  const [ready, setReady] = useState(false);
  const [pulse, setPulse] = useState(0);
  const [shownTide, setShownTide] = useState(p.tideLevel);
  const tideRef = useRef(p.tideLevel);

  const feats = p.scenario.segments.features;
  const byId = useMemo(() => new Map(feats.map((f) => [f.properties.id, f])), [feats]);
  const ut = useMemo(() => new Set(p.undertowIds), [p.undertowIds]);
  const td = useMemo(() => new Set(p.todayIds), [p.todayIds]);

  // ---- map setup ----
  useEffect(() => {
    if (!box.current) return;
    const map = new maplibregl.Map({
      container: box.current, style: STYLE, center: p.scenario.center, zoom: 15, bearing: p.scenario.bearing, pitch: PITCH,
      maxPitch: 70, attributionControl: { compact: true }, dragRotate: true,
    });
    mapRef.current = map;
    let ok = false;
    map.on("style.load", () => { ok = true; });
    const t = setTimeout(() => { if (!ok) map.setStyle(BLANK); }, 6000);
    const overlay = new MapboxOverlay({ interleaved: false, layers: [] });
    overlayRef.current = overlay;
    map.addControl(overlay as unknown as maplibregl.IControl);
    map.on("rotate", () => p.onBearing(map.getBearing()));
    const ro = new ResizeObserver(() => map.resize());
    ro.observe(box.current);
    map.once("load", () => {
      map.resize();
      const cam = map.cameraForBounds(p.scenario.bounds, { padding: { top: 110, bottom: 190, left: 120, right: 520 }, bearing: p.scenario.bearing });
      if (cam) map.jumpTo({ ...cam, bearing: p.scenario.bearing, pitch: PITCH });
      setReady(true);
    });
    return () => { clearTimeout(t); ro.disconnect(); map.remove(); mapRef.current = null; overlayRef.current = null; setReady(false); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p.scenario]);

  // ---- 2D / 3D ----
  useEffect(() => {
    const m = mapRef.current;
    if (m && ready) m.flyTo({ pitch: p.threeD ? PITCH : 0, duration: reduce() ? 0 : 1100, essential: true });
  }, [p.threeD, ready]);

  // ---- fade the basemap for the groundwater view ----
  useEffect(() => {
    const m = mapRef.current;
    if (m) m.getCanvas().style.opacity = p.waterOn ? "0.28" : "1";
  }, [p.waterOn, ready]);

  // ---- fly to the repaired streets ----
  useEffect(() => {
    const m = mapRef.current;
    if (!m || !ready || !p.focus || !p.focus.ids.length) return;
    const pts = p.focus.ids.flatMap((id) => byId.get(id)?.geometry.coordinates ?? []);
    if (!pts.length) return;
    const b = new maplibregl.LngLatBounds(pts[0], pts[0]);
    pts.forEach((c) => b.extend(c));
    m.fitBounds(b, { padding: { top: 140, bottom: 220, left: 160, right: 540 }, maxZoom: 17, duration: reduce() ? 0 : 1800, bearing: p.scenario.bearing, pitch: p.threeD ? PITCH : 0 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p.focus?.nonce]);

  // ---- compass: back to the bearing where the island runs left to right ----
  useEffect(() => {
    if (p.compassNonce) mapRef.current?.easeTo({ bearing: p.scenario.bearing, duration: reduce() ? 0 : 900 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p.compassNonce]);

  // ---- ease the tide level so the ground tint fades smoothly between months ----
  useEffect(() => {
    if (reduce()) { tideRef.current = p.tideLevel; setShownTide(p.tideLevel); return; }
    let raf = 0, start = 0;
    const from = tideRef.current;
    const tick = (now: number) => {
      start ||= now;
      const k = Math.min(1, (now - start) / 900), e = 1 - Math.pow(1 - k, 3);
      tideRef.current = from + (p.tideLevel - from) * e;
      setShownTide(tideRef.current);
      if (k < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [p.tideLevel]);

  // ---- slow pulse for the repair glow and the king tide ground tint ----
  useEffect(() => {
    if (reduce() || !(p.undertowIds.length || p.kingTide)) return;
    const id = setInterval(() => setPulse((performance.now() % 4200) / 4200), 70);
    return () => clearInterval(id);
  }, [p.undertowIds.length, p.kingTide]);

  // ---- deck layers ----
  useEffect(() => {
    const overlay = overlayRef.current;
    if (!overlay) return;
    const path = (f: SegFeature) => f.geometry.coordinates;
    const level = Math.pow(Math.max(0, Math.min(1, shownTide)), 1.5);       // calm months stay almost clear
    const breathe = p.kingTide && !reduce() ? 0.82 + 0.18 * (0.5 + 0.5 * Math.sin(pulse * Math.PI * 2 * 1.0)) : 1;
    const wave = reduce() ? 0.5 : 0.5 + 0.5 * Math.sin(pulse * Math.PI * 2);
    const lowIds = new Set(p.scenario.water.features.map((w) => w.properties.segment));
    const ids = (s: Set<string>) => feats.filter((f) => s.has(f.properties.id));
    const common = { widthUnits: "pixels" as const, capRounded: true, jointRounded: true };

    const lowSegs = feats.filter((f) => lowIds.has(f.properties.id));
    const layers = [
      // king tide: the low-lying ground takes on a soft blue wash that rises with the tide
      ...(!p.waterOn ? [[150, 26], [100, 36], [56, 46]] : []).map(([w, a], i) => new PathLayer<SegFeature>({
        ...common, id: `tide-ground-${i}`, data: lowSegs, getPath: path, getWidth: w,
        getColor: [...BLUE, Math.round(a * level * breathe)] as [number, number, number, number],
        updateTriggers: { getColor: [level, breathe] },
      })),
      ...(p.waterOn ? [[120, 16], [78, 24], [42, 34]] : []).map(([w, a], i) => new PathLayer<SegFeature>({
        ...common, id: `water-glow-${i}`, data: feats.filter((f) => lowIds.has(f.properties.id)), getPath: path, getWidth: w,
        getColor: [...BLUE, a] as [number, number, number, number], capRounded: true,
      })),
      p.waterOn && new PolygonLayer({
        id: "water-contours", data: p.scenario.water.features, getPolygon: (d) => d.geometry.coordinates, filled: false, stroked: true,
        getLineColor: [150, 200, 255, 110], getLineWidth: 1, lineWidthUnits: "pixels",
      }),
      new PathLayer<SegFeature>({
        ...common, id: "dmg-glow", data: feats, getPath: path,
        getWidth: (f) => 12 + f.properties.risk * 22,
        getColor: (f) => [...ORANGE, Math.round(Math.pow(f.properties.risk, 2) * 60)] as [number, number, number, number],
      }),
      new PathLayer<SegFeature>({
        ...common, id: "dmg", data: feats, getPath: path, pickable: true, autoHighlight: true, highlightColor: [255, 255, 255, 90],
        getWidth: (f) => 2.5 + f.properties.risk * 3.5,
        getColor: (f) => [...ORANGE, Math.round(70 + 150 * f.properties.risk)] as [number, number, number, number],
        onClick: ({ object }) => p.onSelect(object ? (object as SegFeature).properties : null),
      }),
      new PathLayer<SegFeature>({
        ...common, id: "route", data: p.scenario.route.features, getPath: path, getWidth: 2.2, getColor: [...PAPER, 190],
        extensions: [new PathStyleExtension({ dash: true })],
        ...({ getDashArray: [4, 3], dashJustified: true } as object),
      }),
      p.compare && new PathLayer<SegFeature>({
        ...common, id: "today", data: ids(td), getPath: path, getWidth: 9, getColor: [...VIOLET, 215],
      }),
      new PathLayer<SegFeature>({
        ...common, id: "ut-glow", data: ids(ut), getPath: path, getWidth: 30 + wave * 18, getColor: [...BLUE, Math.round(55 + wave * 60)] as [number, number, number, number],
        updateTriggers: { getWidth: [pulse], getColor: [pulse] },
      }),
      new PathLayer<SegFeature>({
        ...common, id: "ut", data: ids(ut), getPath: path, getWidth: 7, getColor: [255, 255, 255, 255],
      }),
      p.selectedId && new PathLayer<SegFeature>({
        ...common, id: "sel", data: feats.filter((f) => f.properties.id === p.selectedId), getPath: path, getWidth: 14, getColor: [255, 255, 255, 60],
      }),
      new ScatterplotLayer({
        id: "hospital", data: [p.scenario.hospital], getPosition: (d) => d.coord, getRadius: 9, radiusUnits: "pixels",
        getFillColor: [...BLUE, 255], getLineColor: [255, 255, 255, 255], stroked: true, getLineWidth: 2, lineWidthUnits: "pixels",
      }),
      new TextLayer({
        id: "hospital-label", data: [p.scenario.hospital], getPosition: (d) => d.coord, getText: (d) => d.name, getSize: 12,
        getColor: [...PAPER, 220], getPixelOffset: [0, -20], fontFamily: "Inter Tight, system-ui, sans-serif", background: false,
      }),
    ].filter((l): l is NonNullable<typeof l> & object => typeof l === "object" && l !== null);
    overlay.setProps({ layers, getCursor: ({ isHovering }: { isHovering: boolean }) => (isHovering ? "pointer" : "grab") });
  }, [ready, feats, p.scenario, shownTide, p.kingTide, p.waterOn, p.compare, ut, td, p.selectedId, pulse]);

  return <div ref={box} className="fixed inset-0" aria-label="Map of Miami Beach roads" />;
}
