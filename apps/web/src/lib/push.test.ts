import { describe, expect, it } from 'vitest';
import { urlBase64ToUint8Array } from './push';

describe('urlBase64ToUint8Array', () => {
  it('base64url 을 바이트 배열로 변환한다', () => {
    // "hi" => base64 "aGk=" => base64url "aGk"
    const out = urlBase64ToUint8Array('aGk');
    expect(Array.from(out)).toEqual([104, 105]); // 'h','i'
  });

  it('- 와 _ (base64url) 를 올바르게 디코드한다', () => {
    // 0xff 0xfe => base64 "//4=" => base64url "__4"
    const out = urlBase64ToUint8Array('__4');
    expect(Array.from(out)).toEqual([255, 254]);
  });
});
