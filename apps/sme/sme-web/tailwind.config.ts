import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Approved brand color schema (component-kit reference, not yet applied to
        // any page — wire these into specific screens once they're picked).
        // Semantic role names map onto the reference's brand-named swatches:
        //   primary          = Mint       #17996e — primary actions, positive money, AI confidence
        //   primary.strong   = Deep mint  #0f6b4d — hover/pressed, small text on primary.tint
        //   primary.tint     = derived light mint surface (success banners, subtle fills)
        //   secondary        = Terracotta #ee9077 — time/attention: due dates, escrow, warmth
        //   secondary.tint   = derived light terracotta surface
        //   background       = Sand       #f1ede6 — app ground
        //   surface          = Paper      #fffdf9 — cards
        //   ink              = Ink        #1b1a18 — headlines, text, outlines
        // Rule from the reference: max two of primary/secondary/ink as a background
        // per screen.
        primary: {
          DEFAULT: "#17996e",
          strong: "#0f6b4d",
          tint: "#e3f3ec",
        },
        secondary: {
          DEFAULT: "#ee9077",
          tint: "#fceae4",
        },
        background: "#f1ede6",
        surface: "#fffdf9",
        ink: "#1b1a18",
      },
    },
  },
  plugins: [],
};

export default config;
