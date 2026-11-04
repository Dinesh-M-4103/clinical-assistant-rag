import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { useCreatePatient } from '@/api/hooks/patients';
import { ApiError } from '@/api/client';
import { GENDERS, patientCreateSchema, type PatientCreate } from '@/api/schemas';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogBody,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Field, Input, Select, Textarea } from '@/components/ui/field';
import { Spinner } from '@/components/ui/spinner';
import { describeError } from '@/lib/errors';
import { useWorkspace } from '@/features/workspace/workspaceStore';

const DEFAULTS = { uhid: '', name: '', gender: 'female', summary: '' } as const;

function AddPatientForm({ onDone }: { onDone: () => void }) {
  const navigate = useNavigate();
  const createPatient = useCreatePatient();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<PatientCreate>({
    resolver: zodResolver(patientCreateSchema),
    defaultValues: DEFAULTS,
  });

  const submit = handleSubmit(async (values) => {
    try {
      const patient = await createPatient.mutateAsync({
        ...values,
        summary: values.summary || undefined,
      });
      onDone();
      navigate(`/patients/${encodeURIComponent(patient.uhid)}`);
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setError('uhid', { message: 'A patient with this UHID already exists' });
      } else {
        setError('root', { message: describeError(error) });
      }
    }
  });

  return (
    <form onSubmit={submit} noValidate className="flex min-h-0 flex-1 flex-col">
      <DialogBody className="space-y-4">
        <Field label="Full name" error={errors.name?.message}>
          {({ id, describedBy, invalid }) => (
            <Input
              id={id}
              autoComplete="off"
              aria-describedby={describedBy}
              aria-invalid={invalid}
              {...register('name')}
            />
          )}
        </Field>
        <Field label="UHID" error={errors.uhid?.message} hint="Unique hospital ID, e.g. MG25001">
          {({ id, describedBy, invalid }) => (
            <Input
              id={id}
              autoComplete="off"
              aria-describedby={describedBy}
              aria-invalid={invalid}
              {...register('uhid')}
            />
          )}
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Age" error={errors.age?.message}>
            {({ id, describedBy, invalid }) => (
              <Input
                id={id}
                type="number"
                inputMode="numeric"
                min={0}
                max={130}
                aria-describedby={describedBy}
                aria-invalid={invalid}
                {...register('age', { valueAsNumber: true })}
              />
            )}
          </Field>
          <Field label="Gender">
            {({ id }) => (
              <Select id={id} {...register('gender')}>
                {GENDERS.map((gender) => (
                  <option key={gender} value={gender}>
                    {gender.charAt(0).toUpperCase() + gender.slice(1)}
                  </option>
                ))}
              </Select>
            )}
          </Field>
        </div>
        <Field label="Clinical summary (optional)" error={errors.summary?.message}>
          {({ id, describedBy, invalid }) => (
            <Textarea
              id={id}
              rows={3}
              aria-describedby={describedBy}
              aria-invalid={invalid}
              {...register('summary')}
            />
          )}
        </Field>
        {errors.root && (
          <p role="alert" className="rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">
            {errors.root.message}
          </p>
        )}
      </DialogBody>
      <DialogFooter>
        <Button variant="secondary" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" disabled={createPatient.isPending}>
          {createPatient.isPending && <Spinner />}
          Add patient
        </Button>
      </DialogFooter>
    </form>
  );
}

export function AddPatientDialog() {
  const open = useWorkspace((state) => state.addPatientOpen);
  const setOpen = useWorkspace((state) => state.setAddPatientOpen);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add patient</DialogTitle>
          <DialogDescription>
            Create a record, then upload their reports to start asking questions.
          </DialogDescription>
        </DialogHeader>
        <AddPatientForm onDone={() => setOpen(false)} />
      </DialogContent>
    </Dialog>
  );
}
