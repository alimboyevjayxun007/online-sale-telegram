"use client";
import { useQuery } from "@tanstack/react-query";
import { api, type Catalog, type Me } from "@/lib/api";

export const useMe = () => useQuery({ queryKey: ["me"], queryFn: () => api.get<Me>("/me"), staleTime: 10_000 });
export const useCatalog = () => useQuery({ queryKey: ["catalog"], queryFn: () => api.get<Catalog>("/catalog"), staleTime: 30_000 });
