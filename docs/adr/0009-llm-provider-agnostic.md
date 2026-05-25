# ADR-0009: LLM Provider Agnostic Design

**Status:** Accepted
**Date:** 2026-05-25
**Deciders:** Augustin Chan

## Context

The initial scaffold listed `openai>=1.0` as the only LLM dependency. While the `openai` SDK speaks a wire format compatible with Ollama and vLLM, it creates brand confusion and locks out providers that may outperform on formula translation tasks.

Additionally, designing for acquisition (see ADR-0010) requires avoiding deep coupling to any single cloud/AI provider.

## Decision

The translation engine should be **LLM provider agnostic**. The interface between the translator and the LLM should be an internal abstraction, not a direct SDK dependency.

Initially this can be as simple as the `openai` SDK pointed at configurable endpoints (which covers OpenAI, Anthropic-compatible proxies, Ollama, vLLM). The architecture should allow swapping to `litellm`, `anthropic`, or raw `httpx` without changing the translation engine.

## Rationale

- Anthropic Claude may significantly outperform GPT on structured code transformation tasks
- Enterprise customers may mandate specific providers (or no external providers at all)
- An acquirer may have their own LLM infrastructure
- The `openai` SDK appearing as a dependency creates the impression that OpenAI is required

## Consequences

- LLM calls in the translation engine should go through an internal interface/protocol
- Provider selection via `--llm-provider` CLI flag and configuration
- Local-first (Ollama/vLLM) must remain a first-class option per the safety model
- The `[llm]` optional extra may need to support multiple provider SDKs
