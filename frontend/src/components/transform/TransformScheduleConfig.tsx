import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';

interface TransformScheduleConfigProps {
  scheduleCron: string;
  scheduleEnabled: boolean;
  onCronChange: (cron: string) => void;
  onEnabledChange: (enabled: boolean) => void;
}

const CRON_PRESETS = [
  { label: '毎時', value: '0 * * * *' },
  { label: '毎日 0:00', value: '0 0 * * *' },
  { label: '毎週月曜', value: '0 0 * * 1' },
  { label: '毎月1日', value: '0 0 1 * *' },
];

export function TransformScheduleConfig({
  scheduleCron, scheduleEnabled, onCronChange, onEnabledChange,
}: TransformScheduleConfigProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={scheduleEnabled}
          onChange={(e) => onEnabledChange(e.target.checked)}
          id="schedule-enabled"
        />
        <Label htmlFor="schedule-enabled">スケジュール実行を有効にする</Label>
      </div>

      {scheduleEnabled && (
        <div className="space-y-2">
          <Label>Cron式</Label>
          <Input
            value={scheduleCron}
            onChange={(e) => onCronChange(e.target.value)}
            placeholder="0 0 * * *"
          />
          <div className="flex gap-2 flex-wrap">
            {CRON_PRESETS.map((preset) => (
              <Button
                key={preset.value}
                variant="outline"
                size="sm"
                type="button"
                onClick={() => onCronChange(preset.value)}
              >
                {preset.label}
              </Button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
