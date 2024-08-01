export type StoreStoreType = {
  hasStore: boolean;
  validApiKey: boolean;
  hasApiKey: boolean;
  loadingApiKey: boolean;
  checkHasStore: (hasStore: { enabled: boolean }) => void;
  updateValidApiKey: (validApiKey: boolean) => void;
  updateHasApiKey: (hasApiKey: boolean) => void;
  updateLoadingApiKey: (loadingApiKey: boolean) => void;
  fetchApiData: () => Promise<void>;
};
