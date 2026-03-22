export const MOCK_SUMMARY_DELAY_MS = 1600

export const MOCK_STAGES = [
  { stage: 'queued', duration: 2500 },
  { stage: 'persisting_upload', duration: 3000 },
  { stage: 'validating_video', duration: 2500 },
  { stage: 'uploading_to_gemini', duration: 3000 },
  { stage: 'waiting_for_gemini', duration: 4000 },
  { stage: 'generating_summary', duration: 3500 },
]

export const MOCK_SUMMARY = {
  relational_orientation: {
    description: 'values deep emotional connection, frequently engages with relationship advice and vulnerability content',
    weight: 0.12,
  },
  creativity: {
    description: 'high aesthetic sensibility, drawn to visual art, DIY, and experimental music',
    weight: 0.18,
  },
  intellectualism: {
    description: 'engages with science, philosophy, and long-form educational content',
    weight: 0.1,
  },
  humor: {
    description: 'dry, self-deprecating humor with a preference for absurdist content',
    weight: 0.15,
  },
  interests: {
    description: 'fitness, cooking, personal finance, and travel',
    weight: 0.2,
  },
  cultural_identity: {
    description: 'strong engagement with Latino culture, bilingual content, heritage and identity themes',
    weight: 0.08,
  },
  political_orientation: {
    description: 'center-left, engages with social justice content and progressive policy commentary',
    weight: 0.17,
  },
}
