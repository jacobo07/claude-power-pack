import React from 'react';
import { useQuery, gql } from '@apollo/client';

// Inline gql operation carrying violation (c): duplicate `id` field.
const ME = gql`
  query Me {
    me {
      id
      name
      id
    }
  }
`;

export function App(): JSX.Element {
  const { data, loading, error } = useQuery(ME);
  if (loading) return <span>Loading…</span>;
  if (error) return <span role="alert">{error.message}</span>;
  return <span>{data?.me?.name ?? 'anonymous'}</span>;
}
