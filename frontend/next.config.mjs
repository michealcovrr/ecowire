/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    // Allow data: URLs and external sources for QR codes and Cloudinary media
    dangerouslyAllowSVG: true,
    contentDispositionType: "attachment",
    remotePatterns: [
      { protocol: "https", hostname: "res.cloudinary.com" },
      { protocol: "http", hostname: "localhost" },
    ],
  },
};

export default nextConfig;
