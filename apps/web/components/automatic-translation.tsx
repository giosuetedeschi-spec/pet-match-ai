"use client";

import { useEffect, useState } from "react";

type TextState = { source: string; translated: string };
type Target = { node: Text | Element; attribute?: string };
const textStates = new WeakMap<Text, TextState>();
const attributeStates = new WeakMap<Element, Map<string, TextState>>();
const translatedAttributes = ["alt", "aria-label", "placeholder", "title"];

function getState(target: Target) {
  if (target.node instanceof Text) return textStates.get(target.node);
  return attributeStates.get(target.node)?.get(target.attribute ?? "");
}
function setState(target: Target, state: TextState) {
  if (target.node instanceof Text) textStates.set(target.node, state);
  else {
    const byName = attributeStates.get(target.node) ?? new Map<string, TextState>();
    byName.set(target.attribute ?? "", state); attributeStates.set(target.node, byName);
  }
}
function read(target: Target) { return target.node instanceof Text ? target.node.data : target.node.getAttribute(target.attribute ?? "") ?? ""; }
function write(target: Target, value: string) { if (target.node instanceof Text) target.node.data = value; else target.node.setAttribute(target.attribute ?? "", value); }

export default function AutomaticTranslation() {
  const [locale, setLocale] = useState<"it" | "en">("it");
  useEffect(() => { if (localStorage.getItem("petmatch-locale") === "en") setLocale("en"); }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
    let disposed = false;
    let writingTranslations = false;
    const queue = new Map<string, Target>();
    const nodeIds = new WeakMap<Node, number>(); let nextNodeId = 1;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const ignoredElement = (element: Element) => Boolean(element.closest("script,style,noscript,code,pre,[data-no-translate]"));
    const ignoredText = (node: Text) => !node.data.trim() || !node.parentElement || Boolean(node.parentElement.closest("script,style,noscript,textarea,input,select,option,code,pre,[data-no-translate]"));
    const key = (target: Target) => { let id = nodeIds.get(target.node); if (!id) { id = nextNodeId++; nodeIds.set(target.node, id); } return `${id}:${target.attribute ?? "text"}`; };
    const schedule = () => {
      if (timer) clearTimeout(timer);
      timer = setTimeout(async () => {
        const targets = [...queue.values()].filter((target) => target.node.isConnected); queue.clear();
        for (let offset = 0; offset < targets.length; offset += 50) {
          const batch = targets.slice(offset, offset + 50);
          try {
            const response = await fetch("/api/translate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ target: locale, texts: batch.map((target) => getState(target)?.source ?? read(target)) }) });
            if (!response.ok) continue;
            const result = await response.json() as { translations: string[] };
            if (disposed) return;
            writingTranslations = true;
            batch.forEach((target, index) => {
              const source = getState(target)?.source ?? read(target);
              const translated = result.translations[index] ?? source;
              setState(target, { source, translated }); write(target, translated);
            });
            writingTranslations = false;
          } catch { writingTranslations = false; }
        }
      }, 80);
    };
    const visit = (node: Node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        const target: Target = { node: node as Text }; const old = getState(target); const current = read(target);
        if (old && current === old.translated) return;
        if (old) setState(target, { source: current, translated: "" });
        if (!ignoredText(node as Text)) queue.set(key(target), target);
        return;
      }
      if (node.nodeType === Node.ELEMENT_NODE) {
        const element = node as Element;
        if (ignoredElement(element)) return;
        for (const attribute of translatedAttributes) {
          const value = element.getAttribute(attribute); if (!value?.trim()) continue;
          const target: Target = { node: element, attribute }; const old = getState(target);
          if (old && value === old.translated) continue;
          if (old) setState(target, { source: value, translated: "" });
          queue.set(key(target), target);
        }
      }
      node.childNodes.forEach(visit);
    };
    const restore = () => {
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT); let node: Node | null;
      writingTranslations = true;
      while ((node = walker.nextNode())) {
        if (node.nodeType === Node.TEXT_NODE) {
          const text = node as Text; const state = textStates.get(text);
          if (state && text.data === state.translated) text.data = state.source;
          textStates.delete(text);
        } else {
          const element = node as Element; const states = attributeStates.get(element);
          states?.forEach((state, attribute) => { if (element.getAttribute(attribute) === state.translated) element.setAttribute(attribute, state.source); });
          attributeStates.delete(element);
        }
      }
      writingTranslations = false;
    };
    if (locale === "it") restore(); else { visit(document.body); schedule(); }
    const observer = new MutationObserver((mutations) => {
      if (writingTranslations || locale === "it") return;
      mutations.forEach((mutation) => {
        if (mutation.type === "characterData" || mutation.type === "attributes") visit(mutation.target);
        mutation.addedNodes.forEach(visit);
      });
      if (queue.size) schedule();
    });
    observer.observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: translatedAttributes });
    return () => { disposed = true; observer.disconnect(); if (timer) clearTimeout(timer); };
  }, [locale]);

  return <div className="locale-control" data-no-translate><button className="locale-toggle" type="button" onClick={() => { const next = locale === "it" ? "en" : "it"; localStorage.setItem("petmatch-locale", next); setLocale(next); }}>{locale === "it" ? "English" : "Italiano"}</button><span>{locale === "it" ? "Traduzione automatica" : "Automatic translation"}</span></div>;
}
