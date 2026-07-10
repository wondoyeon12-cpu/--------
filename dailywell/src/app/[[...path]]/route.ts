import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const WP_ORIGIN = "https://wondoyeon12.mycafe24.com";

// 우리 사이트 도메인 목록 (리다이렉트 루프 방지)
const OWN_DOMAINS = ["dailywell.co.kr", "www.dailywell.co.kr"];

// Vercel WAF 우회를 위해 admin-ajax.php 경로 매핑
function getWpUrl(pathStr: string, searchStr: string): string {
  if (pathStr === "wp-ajax") {
    return `${WP_ORIGIN}/wp-admin/admin-ajax.php${searchStr}`;
  }
  return `${WP_ORIGIN}/${pathStr}${searchStr}`;
}

// 헤더 복사 및 CSRF 방지를 위한 호스트/오리진/레퍼러 재작성
function getForwardedHeaders(request: NextRequest): Headers {
  const headers = new Headers();
  
  request.headers.forEach((value, key) => {
    const lowerKey = key.toLowerCase();
    if (
      lowerKey !== "host" &&
      lowerKey !== "connection" &&
      lowerKey !== "content-length" &&
      lowerKey !== "accept-encoding"
    ) {
      headers.set(key, value);
    }
  });

  // Origin 헤더가 존재하면 대상 도메인(WP_ORIGIN)으로 우회
  const origin = request.headers.get("origin");
  if (origin) {
    headers.set("origin", WP_ORIGIN);
  }

  // Referer 헤더가 존재하면 대상 도메인 주소로 교체 (CSRF 차단 우회)
  const referer = request.headers.get("referer");
  if (referer) {
    let newReferer = referer;
    
    // 현재 요청이 들어온 Host 도메인을 동적으로 추출하여 WP_ORIGIN으로 변환 (로컬 개발 환경 및 Vercel 임시 도메인 대응)
    const host = request.headers.get("x-forwarded-host") || request.headers.get("host") || "";
    if (host) {
      const escapeRegExp = (str: string) => str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const hostRegex = new RegExp(`https?:\\/\\/${escapeRegExp(host)}`, "g");
      newReferer = newReferer.replace(hostRegex, WP_ORIGIN);
    }

    newReferer = newReferer.replace(/https?:\/\/dailywell\.co\.kr/g, WP_ORIGIN);
    newReferer = newReferer.replace(/https?:\/\/www\.dailywell\.co\.kr/g, WP_ORIGIN);
    // wp-ajax 레퍼러도 원본 admin-ajax.php로 인식하도록 변환
    newReferer = newReferer.replace(/\/wp-ajax/g, "/wp-admin/admin-ajax.php");
    headers.set("referer", newReferer);
  }

  // User-Agent 기본 설정 보장
  if (!headers.has("user-agent")) {
    headers.set(
      "user-agent",
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    );
  }

  return headers;
}

/**
 * WordPress fetch - 리다이렉트 루프 해결 버전
 */
async function fetchFromWordPress(
  wpUrl: string,
  headers: Headers,
  attempt = 0,
  visitedPaths: Set<string> = new Set()
): Promise<Response | null> {
  if (attempt > 10) return null;

  // 이미 방문한 경로면 루프 → 중단
  const urlObj = new URL(wpUrl);
  const pathKey = urlObj.pathname + urlObj.search;
  if (visitedPaths.has(pathKey)) return null;
  visitedPaths.add(pathKey);

  // Headers 인스턴스를 일반 객체로 변환하여 Host 재정의 필터 우회
  const headersObj: Record<string, string> = {};
  headers.forEach((value, key) => {
    headersObj[key] = value;
  });
  // Cafe24 가상 호스트 보안 정책 우회를 위해 Host 헤더는 원본 도메인(wondoyeon12.mycafe24.com)으로 설정
  headersObj["Host"] = new URL(WP_ORIGIN).hostname;
  headersObj["X-Forwarded-Host"] = "dailywell.co.kr";
  headersObj["X-Forwarded-Proto"] = "https";

  const res = await fetch(wpUrl, {
    headers: headersObj,
    redirect: "manual",
    cache: "no-store",
  });

  // 리다이렉트 응답 처리
  if (res.status >= 300 && res.status < 400) {
    const location = res.headers.get("location");
    if (!location) return null;

    try {
      const redirectUrl = new URL(location, WP_ORIGIN);

      // 우리 도메인으로 리다이렉트 → 경로만 추출해서 WP_ORIGIN으로 재요청
      if (OWN_DOMAINS.includes(redirectUrl.hostname)) {
        const wpRedirectUrl = `${WP_ORIGIN}${redirectUrl.pathname}${redirectUrl.search}`;
        return fetchFromWordPress(wpRedirectUrl, headers, attempt + 1, visitedPaths);
      }

      // WordPress 도메인 내부 리다이렉트 → 그대로 따라가기
      if (redirectUrl.hostname === new URL(WP_ORIGIN).hostname) {
        return fetchFromWordPress(redirectUrl.toString(), headers, attempt + 1, visitedPaths);
      }
    } catch {
      // URL 파싱 오류 무시
    }
    return null;
  }

  return res;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path?: string[] }> }
) {
  const { path } = await params;

  // wp-admin은 WordPress 원본으로 직접 리다이렉트 (보안/기능 보장, 단 admin-ajax.php는 프록시 처리)
  const pathStr = path ? path.join("/") : "";
  if ((pathStr.startsWith("wp-admin") && !pathStr.includes("admin-ajax.php")) || pathStr.startsWith("wp-login")) {
    return NextResponse.redirect(`${WP_ORIGIN}/${pathStr}`);
  }

  const searchStr = request.nextUrl.search || "";
  const wpUrl = getWpUrl(pathStr, searchStr);

  try {
    const forwardedHeaders = getForwardedHeaders(request);
    const wpRes = await fetchFromWordPress(wpUrl, forwardedHeaders);

    if (!wpRes) {
      return new NextResponse("페이지를 찾을 수 없습니다.", {
        status: 404,
        headers: { "Content-Type": "text/html; charset=utf-8" },
      });
    }

    if (!wpRes.ok) {
      return new NextResponse(
        `오류가 발생했습니다. (${wpRes.status})`,
        {
          status: wpRes.status,
          headers: { "Content-Type": "text/html; charset=utf-8" },
        }
      );
    }

    const contentType = wpRes.headers.get("content-type") || "text/html";
    const isHtml = contentType.includes("text/html");
    const isJson = contentType.includes("application/json");

    if (isHtml || isJson) {
      let bodyText = await wpRes.text();

      // WordPress 내부 URL(mycafe24 + 우리 도메인 양쪽)을 현재 Vercel 도메인으로 교체
      const host =
        request.headers.get("x-forwarded-host") ||
        request.headers.get("host") ||
        "";
      if (host) {
        // mycafe24 URL 교체
        bodyText = bodyText.replace(
          /https?:\/\/wondoyeon12\.mycafe24\.com/g,
          `https://${host}`
        );
        bodyText = bodyText.replace(
          /https?:\\\/\\\/wondoyeon12\.mycafe24\.com/g,
          `https:\\\/\\\/${host}`
        );
        // www.dailywell.co.kr URL 교체 (WordPress siteurl이 www로 설정된 경우)
        bodyText = bodyText.replace(
          /https?:\/\/www\.dailywell\.co\.kr/g,
          `https://${host}`
        );
        bodyText = bodyText.replace(
          /https?:\\\/\\\/www\.dailywell\.co\.kr/g,
          `https:\\\/\\\/${host}`
        );

        if (isHtml) {
          // 구글 서치콘솔 인증 메타태그 강제 주입
          bodyText = bodyText.replace(
            "<head>",
            `<head>\n    <meta name="google-site-verification" content="iaO9GZbiY7GXMzZQgU-Ehw4QzNW82INHHd8v64W2yx8" />`
          );
        }
        
        // Vercel WAF 우회: 일반 슬래시 형식 치환
        bodyText = bodyText.replace(
          /https?:\/\/(?:wondoyeon12\.mycafe24\.com|www\.dailywell\.co\.kr|dailywell\.co\.kr)?\/wp-admin\/admin-ajax\.php/g,
          `https://${host}/wp-ajax`
        );
        bodyText = bodyText.replace(
          /\/wp-admin\/admin-ajax\.php/g,
          `/wp-ajax`
        );

        // Vercel WAF 우회: JSON 이스케이프 형식 치환 (스크립트 태그 내부 JSON용)
        bodyText = bodyText.replace(
          /https?:\\\/\\\/(?:wondoyeon12\.mycafe24\.com|www\.dailywell\.co\.kr|dailywell\.co\.kr)?\\\/wp-admin\\\/admin-ajax\.php/g,
          `https:\\\/\\\/${host}\\\/wp-ajax`
        );
        bodyText = bodyText.replace(
          /\\\/wp-admin\\\/admin-ajax\.php/g,
          `\\\/wp-ajax`
        );
      }

      return new NextResponse(bodyText, {
        headers: {
          "Content-Type": contentType,
          // 캐시로 인해 수정 코드가 미반영되는 현상 방지하기 위해 캐시 무효화 설정
          "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        },
      });
    }

    // HTML이 아닌 콘텐츠 (이미지, PDF 등)를 ArrayBuffer로 안전하게 전달
    const buffer = await wpRes.arrayBuffer();
    return new NextResponse(buffer, {
      headers: {
        "Content-Type": contentType,
        // 캐시로 인해 수정 코드가 미반영되는 현상 방지하기 위해 캐시 무효화 설정
        "Cache-Control": "public, max-age=86400",
      },
    });
  } catch (error) {
    console.error("[DailywellProxy] catch-all error:", error);
    return new NextResponse("서버 오류가 발생했습니다.", {
      status: 500,
      headers: { "Content-Type": "text/html; charset=utf-8" },
    });
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path?: string[] }> }
) {
  const { path } = await params;
  const pathStr = path ? path.join("/") : "";
  const searchStr = request.nextUrl.search || "";
  const wpUrl = getWpUrl(pathStr, searchStr);

  try {
    const body = request.body ? await request.arrayBuffer() : undefined;
    const forwardedHeaders = getForwardedHeaders(request);

    // Headers 인스턴스를 일반 객체로 변환하여 Host 재정의 필터 우회
    const headersObj: Record<string, string> = {};
    forwardedHeaders.forEach((value, key) => {
      headersObj[key] = value;
    });
    // Cafe24 가상 호스트 보안 정책 우회를 위해 Host 헤더는 원본 도메인(wondoyeon12.mycafe24.com)으로 설정
    headersObj["Host"] = new URL(WP_ORIGIN).hostname;
    headersObj["X-Forwarded-Host"] = "dailywell.co.kr";
    headersObj["X-Forwarded-Proto"] = "https";

    const wpRes = await fetch(wpUrl, {
      method: "POST",
      headers: headersObj,
      body: body,
      redirect: "manual",
      cache: "no-store",
    });

    // Handle redirects
    if (wpRes.status >= 300 && wpRes.status < 400) {
      const location = wpRes.headers.get("location");
      if (location) {
        const host = request.headers.get("host") || "";
        let newLocation = location;
        if (host) {
          newLocation = newLocation.replace(
            /https?:\/\/wondoyeon12\.mycafe24\.com/g,
            `https://${host}`
          );
          newLocation = newLocation.replace(
            /https?:\/\/www\.dailywell\.co\.kr/g,
            `https://${host}`
          );
        }
        return NextResponse.redirect(newLocation, wpRes.status);
      }
    }

    if (!wpRes.ok) {
      return new NextResponse(`오류가 발생했습니다. (${wpRes.status})`, {
        status: wpRes.status,
        headers: { "Content-Type": "text/html; charset=utf-8" },
      });
    }

    const contentType = wpRes.headers.get("content-type") || "text/html";
    const isHtml = contentType.includes("text/html");
    const isJson = contentType.includes("application/json");

    if (isHtml || isJson) {
      let bodyText = await wpRes.text();
      const host =
        request.headers.get("x-forwarded-host") ||
        request.headers.get("host") ||
        "";
      if (host) {
        bodyText = bodyText.replace(
          /https?:\/\/wondoyeon12\.mycafe24\.com/g,
          `https://${host}`
        );
        bodyText = bodyText.replace(
          /https?:\\\/\\\/wondoyeon12\.mycafe24\.com/g,
          `https:\\\/\\\/${host}`
        );
        bodyText = bodyText.replace(
          /https?:\/\/www\.dailywell\.co\.kr/g,
          `https://${host}`
        );
        bodyText = bodyText.replace(
          /https?:\\\/\\\/www\.dailywell\.co\.kr/g,
          `https:\\\/\\\/${host}`
        );
        
        // Vercel WAF 우회: 일반 슬래시 형식 치환
        bodyText = bodyText.replace(
          /https?:\/\/(?:wondoyeon12\.mycafe24\.com|www\.dailywell\.co\.kr|dailywell\.co\.kr)?\/wp-admin\/admin-ajax\.php/g,
          `https://${host}/wp-ajax`
        );
        bodyText = bodyText.replace(
          /\/wp-admin\/admin-ajax\.php/g,
          `/wp-ajax`
        );

        // Vercel WAF 우회: JSON 이스케이프 형식 치환
        bodyText = bodyText.replace(
          /https?:\\\/\\\/(?:wondoyeon12\.mycafe24\.com|www\.dailywell\.co\.kr|dailywell\.co\.kr)?\\\/wp-admin\\\/admin-ajax\.php/g,
          `https:\\\/\\\/${host}\\\/wp-ajax`
        );
        bodyText = bodyText.replace(
          /\\\/wp-admin\\\/admin-ajax\.php/g,
          `\\\/wp-ajax`
        );
      }
      return new NextResponse(bodyText, {
        headers: {
          "Content-Type": contentType,
        },
      });
    }

    // JSON or other responses (like chatbot API response)
    const resBody = await wpRes.arrayBuffer();
    return new NextResponse(resBody, {
      headers: {
        "Content-Type": contentType,
      },
    });
  } catch (error) {
    console.error("[DailywellProxy] POST catch-all error:", error);
    return new NextResponse("서버 오류가 발생했습니다.", {
      status: 500,
      headers: { "Content-Type": "text/html; charset=utf-8" },
    });
  }
}
