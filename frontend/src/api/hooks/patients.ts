import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { api } from '../endpoints';
import { queryKeys } from './keys';

export function usePatients() {
  return useQuery({ queryKey: queryKeys.patients, queryFn: api.listPatients });
}

export function usePatient(uhid: string) {
  return useQuery({ queryKey: queryKeys.patient(uhid), queryFn: () => api.getPatient(uhid) });
}

/** Errors are surfaced inline by the add-patient form (e.g. duplicate UHID), not as a toast. */
export function useCreatePatient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.createPatient,
    meta: { silent: true },
    onSuccess: (patient) => {
      // A deleted patient's cached reports must never show up for a new patient reusing the UHID.
      queryClient.removeQueries({ queryKey: queryKeys.reports(patient.uhid) });
      queryClient.setQueryData(queryKeys.patient(patient.uhid), patient);
      void queryClient.invalidateQueries({ queryKey: queryKeys.patients, exact: true });
      toast.success(`${patient.name} added`);
    },
  });
}

export function useDeletePatient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.deletePatient,
    // The patient's queries are left to expire: removing them while the page is still mounted
    // makes its observers refetch the deleted patient and log a 404.
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.patients, exact: true });
      toast.success('Patient and all their reports deleted');
    },
  });
}
