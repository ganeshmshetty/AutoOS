export interface BaseResponse<T = any> {
  success: boolean;
  data?: T;
  plainTextResponse: string;
  error?: string;
}

export type OSCommand = () => Promise<BaseResponse>;
