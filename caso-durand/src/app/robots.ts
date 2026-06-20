import type { MetadataRoute } from "next";

// Bloqueia toda indexação por buscadores. Site privado, nunca público.
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      disallow: "/",
    },
  };
}
